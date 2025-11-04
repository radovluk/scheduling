# Scheduling

This repository contains Jupyter notebooks for defining, learning and experimenting with **scheduling problems**:

- **Job Shop Scheduling**
- **RCPSP (Resource-Constrained Project Scheduling)**
- **Multi-Mode RCPSP**
- **RCPSP with Blocking and Preemption**

---

## 📒 Notebooks

| Topic | Notebook | Colab |
|-------|---------|-------|
| Job Shop Scheduling | [jobshop.ipynb](notebooks/jobshop.ipynb) | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR_USERNAME/scheduling-lab/blob/main/notebooks/jobshop.ipynb) |
| RCPSP Basics | [rcpsp.ipynb](notebooks/rcpsp.ipynb) | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR_USERNAME/scheduling-lab/blob/main/notebooks/rcpsp.ipynb) |
| Multi-Mode RCPSP | [multimode_rcpsp.ipynb](notebooks/multimode_rcpsp.ipynb) | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR_USERNAME/scheduling-lab/blob/main/notebooks/multimode_rcpsp.ipynb) |
| RCPSP with Blocking/Preemption | [rcpsp_blocking_preemption.ipynb](notebooks/rcpsp_blocking_preemption.ipynb) | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR_USERNAME/scheduling-lab/blob/main/notebooks/rcpsp_blocking_preemption.ipynb) |

---

## 📂 Data

All input files for the notebooks are in the [`data/`](data/) folder.

---

## 🚀 How to run locally

Install dependencies via Conda:

```bash
conda env create -f environment.yml
conda activate scheduling-lab
jupyter notebook
