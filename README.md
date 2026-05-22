<br>
<p align="center">
  <h1 align="center"><strong>AvatarTex: High-Fidelity Facial Texture Reconstruction from Single-Image Stylized Avatars</strong></h1>
  <h3 align="center">🔥 3DV 2026 🔥 </h3>
  <p align="center">
    <a href="https://www.semanticscholar.org/author/Yuda-Qiu/51152863" target="_blank">Yuda Qiu</a><sup>1*</sup>&emsp;
    <a href="https://github.com/XZT24" target="_blank">Zitong Xiao</a><sup>1*</sup>&emsp;
    <a href="https://yiweizuo.github.io/" target="_blank">Yiwei Zuo</a><sup>1</sup>&emsp;
    <a href="https://www.linkedin.com/in/yezisheng/" target="_blank">Zisheng Ye</a><sup>1</sup>&emsp;
    <a href="https://scholar.google.com/citations?user=Ec6QLl0AAAAJ&hl=en" target="_blank">Weikai Chen</a><sup>3</sup>&emsp;
    <a href="https://dblp.org/pid/60/8294" target="_blank">Xiaoguang Han</a><sup>1,2</sup>
    <br>
    <sup>1</sup>SSE, CUHK-Shenzhen&nbsp;&nbsp;
    <sup>2</sup>Fnii, CUHK-Shenzhen&nbsp;&nbsp;
    <sup>3</sup>Independent Researcher&nbsp;&nbsp;
    <sup>*</sup>Equal Contribution (Alphabetical Order)
  </p>
</p>


<div id="top" align="center">

[![arXiv](https://img.shields.io/badge/arXiv-2512.22939-blue)](https://arxiv.org/abs/2511.06721)

</div>

<div align="center">
  <img src="assets/teaser.png" alt="Illustration" width="96%">
</div>

---

## 🔥 News
- **[2025-11]** Our paper was accept by 3DV2026 ! 🥳 
- **[2025-11]** We release the [paper](https://arxiv.org/abs/2511.06721) for **AvatarTex**.
- **[2026-05]** Texhub is released!

---

## ⭐ Overview
**AvatarTex** is a high-fidelity facial texture reconstruction framework capable of generating both stylized and photorealistic textures from a single image.
Our key insight is that:
1) While **diffusion** models excel at generating diversified textures, they lack explicit UV constraints,
2) Whereas **GANs** provide a well-structured latent space that ensures style and topology consistency.
   
By integrating these strengths, AvatarTex achieves high-quality topology-aligned texture synthesis with both artistic and geometric coherence.

---

## 📖 Framework
<div align="center">
  <img src="assets/framework.png" alt="Framework" width="96%">
</div>

AvatarTex consists of four key components:

**(a)** Dataset Construction 

**(b)** Texture Initialization 

**(c)** Texture Correction

**(d)** Texture Refinement


---

## 📝 TODO
- \[x\] Release paper and github page.
- \[x\] Release the StyleGAN ckpt for Texhub.

---

## 📚 Getting Started
Thanks for waiting! We have released Texhub, please download from the following link: 
<a href="https://drive.google.com/file/d/1F9rtvIYg7ZgTrASFyloTjGBHf9qTKSJU/view?usp=drive_link" target="_blank">Texhub</a>. 

Due to copyright and security concerns associated with directly releasing the TexHub texture dataset, we instead release the trained StyleGAN checkpoint. This checkpoint is trained on a  collection of multi-style texture data curated and created by us. Compared with models trained solely on real texture datasets, it demonstrates significantly stronger expressive capability. Moreover, it can be readily integrated into existing advanced face reconstruction frameworks. We will provide an example in future updates to demonstrate how to use it in practice.

## Environment Setup
Please configure the base environment according to the environment.yml file, as it provides the required dependencies for using the TexHub checkpoint. In addition, to implement face reconstruction frameworks, <a href="https://github.com/NVlabs/nvdiffrast/tree/main" target="_blank">nvdiffrast</a> is often essential. Please follow the instructions provided in the linked repository for installation and setup.

---

## 📬 Contact
If you have questions about the paper, feel free to open an issue or contact:
- **Zitong Xiao**: `120090766@link.cuhk.edu.cn`

---

## 🔗 Citation
If you find our work helpful, please cite:

```bibtex
@article{qiu2025avatartex,
  title={AvatarTex: High-Fidelity Facial Texture Reconstruction from Single-Image Stylized Avatars},
  author={Qiu, Yuda and Xiao, Zitong and Zuo, Yiwei and Ye, Zisheng and Chen, Weikai and Han, Xiaoguang},
  journal={arXiv preprint arXiv:2511.06721},
  year={2025}
}

