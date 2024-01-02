FROM continuumio/miniconda3
# FROM mambaorg/micromamba
WORKDIR /app
# USER $MAMBA_USER
# USER $CONDA_USER

# Create the environment:
COPY env.yaml .
COPY src .
RUN conda env create -f env.yaml
#RUN  micromamba create -f environment.yml && micromamba clean --all --yes

# Override default shell and use bash
SHELL ["conda", "run", "-n", "gg", "/bin/bash", "-c"]
ENTRYPOINT ["conda", "run", "-n", "gg", "python", "-m", "ui.main"]