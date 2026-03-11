from pathlib import Path


def abrir_system_prompt(titulo: str) -> str:
    """
    Le o prompt de sistema a partir da pasta de prompts.
    Parametros:
        titulo: Nome do arquivo de prompt (string)
    Retorna:
        Conteudo do arquivo de prompt (string)
    """
    base_dir: Path = Path(__file__).resolve().parents[1]
    caminho: Path = base_dir / "prompts" / "system" / f"{titulo}.md"

    if not caminho.exists():
        raise Exception(f"O caminho '{str(caminho)}' não existe!")

    with open(str(caminho), "r", encoding="utf-8") as arquivo:
        resultado: str = arquivo.read()

    return resultado


def abrir_txt(src: str) -> str:
    """
    Le um arquivo de texto e retorna seu conteudo.
    Parametros:
        src: Caminho do arquivo (string)
    Retorna:
        Conteudo do arquivo (string)
    """
    src_path: Path = Path(src)

    if not src_path.exists():
        raise Exception(f"Arquivo '{src}' não encontrado")

    with open(src, "r", encoding="utf-8") as arquivo:
        conteudo = arquivo.read()

    return conteudo
