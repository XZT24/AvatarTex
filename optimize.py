import os
import torch
import numpy as np
from PIL import Image
import torch.nn.functional as F
import legacy
import dnnlib
import torch.nn as nn

from prodigyopt import Prodigy

import nvdiffrast.torch as dr
from mesh import load_obj_mesh
import util
import lpips


# This is a simple example demonstrating how to use TexHub
# for the Texture Correction stage in AvatarTex.
# You may refer to this code to integrate TexHub into other
# reconstruction frameworks, such as FFHQ-UV.

def transform_pos(mtx, pos):
    t_mtx = torch.from_numpy(mtx).cuda() if isinstance(mtx, np.ndarray) else mtx
    posw = torch.cat([pos, torch.ones([pos.shape[0], 1]).cuda()], axis=1)
    return torch.matmul(posw, t_mtx.t())[None, ...]


def render(glctx, mtx, pos, pos_idx, uv, uv_idx, tex, resolution, enable_mip, max_mip_level):
    pos_clip = transform_pos(mtx, pos)
    rast_out, rast_out_db = dr.rasterize(glctx, pos_clip, pos_idx, resolution=[resolution, resolution])
    if enable_mip:
        texc, texd = dr.interpolate(uv[None, ...], rast_out, uv_idx, rast_db=rast_out_db, diff_attrs='all')
        color = dr.texture(tex[None, ...], texc, texd, filter_mode='linear-mipmap-linear', max_mip_level=max_mip_level)
    else:
        texc, _ = dr.interpolate(uv[None, ...], rast_out, uv_idx)
        color = dr.texture(tex[None, ...], texc, filter_mode='linear')
    color = color * torch.clamp(rast_out[..., -1:], 0, 1)  # Mask out background.
    return color

def load_texture_and_mesh(tex, mesh_path):
    tex = tex.squeeze(0)
    tex = tex.permute(1, 2, 0)
    tex = torch.flip(tex, dims=[0])
    tex = (tex+1)/2
    tex = tex.contiguous()

    v, f, uv, uvf = load_obj_mesh(mesh_path, with_texture=True)
    v = torch.tensor(v, dtype=torch.float32).cuda()
    f = torch.tensor(f, dtype=torch.int32).cuda()
    uv = torch.tensor(uv, dtype=torch.float32).cuda()
    uvf = torch.tensor(uvf, dtype=torch.int32).cuda()

    return tex, v, f, uv, uvf

def render_mesh_with_texture(tex, mesh_path, resolution=512, enable_mip=True, max_mip_level=9):
    
    tex, v, f, uv, uvf = load_texture_and_mesh(tex, mesh_path)
    v = v*0.6
    use_opengl = False
    glctx = dr.RasterizeGLContext() if use_opengl else dr.RasterizeCudaContext()
    ang = 0.0
    r_rot = np.eye(4)
    dist = 2.0

    proj = util.orthographic_projection(x=0.4, n=1.0, f=200.0)
    r_mv = np.matmul(util.translate(0, 0, -dist), r_rot)
    r_mvp = np.matmul(proj, r_mv).astype(np.float32)

    color = render(glctx, r_mvp, v, f, uv, uvf, tex, resolution, enable_mip, max_mip_level)[0]
    color = color * 2 - 1
    color = color.permute(2,0,1)
    color = color.unsqueeze(0)    
    return color



# Define image loading and pre-processing
def resize_image(image_path, size=(512, 512)):
    image = Image.open(image_path).convert('RGB')
    return (np.array(image.resize(size)) / 255.0)*2-1  


# Main optimization logic
def optimize_latent_z(network_pkl, target_image_path, output_dir, unique3d_topo_obj, hifi_topo_obj, unique3d_tex_path, image_size=512, tex_steps=300, view_steps=80):
    device = torch.device('cuda')

    # Load pre-trained StyleGAN model
    print(f'Loading networks from "{network_pkl}"...')
    with dnnlib.util.open_url(network_pkl) as f:
        G = legacy.load_network_pkl(f)['G_ema'].to(device)  # Generator

    # Load target image
    target_image = resize_image(target_image_path)
    target_image = torch.tensor(target_image).permute(2,0,1).unsqueeze(0).float().to(device)

    # Define perceptual loss
    loss_fn = nn.MSELoss()
    loss_fn_vgg = lpips.LPIPS(net='vgg').to(device) # closer to "traditional" perceptual loss, when used for optimization
    loss_l1 = nn.L1Loss()

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(output_dir+'_view', exist_ok=True)

    z = torch.randn(1, G.z_dim, device=device, requires_grad=True)
    mapping_network = G.mapping

# ------------------stage1---------------------
    w = mapping_network(z, None).detach()
    w.requires_grad = True

    optimizer = Prodigy([w], lr=1.)
    # Optimization loop
    for step in range(tex_steps):
        optimizer.zero_grad()

        # Generate image from z
        generated_image = G.synthesis(w)
        generated_image = F.interpolate(generated_image, size=(image_size, image_size), mode='bilinear', align_corners=False)
        generated_image = (generated_image + 1) / 2  # Normalize to [0, 1]

        # Compute loss
        target_image_norm = (target_image + 1) / 2  # Normalize to [0, 1]
        loss1 = loss_l1(generated_image, target_image_norm)
        loss2 = loss_fn_vgg(generated_image, target_image_norm)
        loss = loss1+loss2


        # Backpropagation
        loss.backward()
        optimizer.step()

        # Logging and saving images
        if step % 50 == 0 or step == tex_steps - 1:
            print(f"Step {step}/{tex_steps}, Loss_vgg: {loss1.item():.4f}, Loss_l1: {loss2.item():.4f}")
            output_image = (generated_image[0].permute(1, 2, 0) * 255).clamp(0, 255).to(torch.uint8).cpu().numpy()
            Image.fromarray(output_image).save(os.path.join(output_dir, f"step_{step:04d}.png"))
    

# ------------------stage2---------------------

    w_init = w.clone().detach()
    generated_image = G.synthesis(w)
    generated_image = F.interpolate(generated_image, size=(image_size, image_size), mode='bilinear', align_corners=False)
    rendered_img = render_mesh_with_texture(generated_image, hifi_topo_obj) # [-1,1]

    gray_image = rendered_img.mean(dim=1, keepdim=True)
    mask_rendered = (gray_image != -1).float()
    mask_rendered = mask_rendered.expand_as(rendered_img)

    unique_tex = resize_image(unique3d_tex_path)
    unique_tex = torch.tensor(unique_tex).permute(2,0,1).unsqueeze(0).float().to(device)
    target_view = render_mesh_with_texture(unique_tex, unique3d_topo_obj) # [-1,1]

    gray_image = target_view.mean(dim=1, keepdim=True)
    mask_view = (gray_image != -1).float()
    mask_view = mask_view.expand_as(target_view)
    
    for step in range(view_steps):
        optimizer.zero_grad()

        # Generate image from z
        generated_image = G.synthesis(w)
        generated_image = F.interpolate(generated_image, size=(image_size, image_size), mode='bilinear', align_corners=False)

        rendered_img = render_mesh_with_texture(generated_image, hifi_topo_obj)
        rendered_img = (rendered_img+1)/2 # [0,1]
        layer_weights = torch.linspace(1, 0.01, w.size(1)).unsqueeze(0).unsqueeze(2).to(w.device)  # (1, 16, 1)
        

        # Compute loss
        target_view_norm = (target_view + 1) / 2 # Normalize to [0, 1]
        loss1 = loss_fn(rendered_img*mask_rendered*mask_view, target_view_norm*mask_rendered*mask_view)*10       
        loss2 = torch.mean(layer_weights * (w - w_init).pow(2))*0.5
        loss3 = loss_fn_vgg(rendered_img*mask_rendered*mask_view, target_view_norm*mask_rendered*mask_view)
        loss = loss3+loss2+loss1

        # Backpropagation
        loss.backward()
        optimizer.step()

        # Logging and saving images
        if step % 50 == 0 or step == view_steps - 1:
            print(f"Step {step}/{view_steps}, Loss_mse: {loss1.item():.4f}, Loss_reg: {loss2.item():.4f},Loss_vgg: {loss3.item():.4f}")
            output_image = ((generated_image[0].permute(1, 2, 0)+1)/2 * 255).clamp(0, 255).to(torch.uint8).cpu().numpy()
            rendered_img = torch.flip(rendered_img, dims=[2])
            output_render = (rendered_img[0].permute(1, 2, 0) * 255).clamp(0, 255).to(torch.uint8).cpu().numpy()
            target_view_norm = torch.flip(target_view_norm, dims=[2])
            output_gt = (target_view_norm[0].permute(1, 2, 0) * 255).clamp(0, 255).to(torch.uint8).cpu().numpy()
            Image.fromarray(output_image).save(os.path.join(output_dir, f"step_view_{step:04d}.png"))
            Image.fromarray(output_render).save(os.path.join(output_dir+'_view', f"step_view_{step:04d}.png"))
            Image.fromarray(output_gt).save(os.path.join(output_dir+'_view', f"step_view_gt_{step:04d}.png"))

    print("Optimization complete.")

# Run the optimization
if __name__ == "__main__":
    network_pkl = "./texhub_ckpt/network-snapshot-010000.pkl"  # Replace with actual path
    init_tex_path = "./data/init_tex.png"  # Replace with actual path
    output_dir = "./output"
    unique3d_topo_obj = './data/unique3d.obj'
    hifi_topo_obj = './data/hifi.obj'
    unique3d_tex_path = './data/unique3d_tex.png'
    optimize_latent_z(network_pkl, init_tex_path, output_dir, unique3d_topo_obj, hifi_topo_obj, unique3d_tex_path)



