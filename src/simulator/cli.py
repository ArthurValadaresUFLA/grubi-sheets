from __future__ import annotations

import csv
import glob
import os
import shlex
from pathlib import Path

import click

from simulator.parser import DataEngine
from simulator.report import OdsReport
from simulator.runner import JavaRunner, ParallelExecutor


def resolve_classpath(cp_inputs: tuple[str, ...]) -> str:
    """Resolve padrões de shell (glob) e caminhos (pastas/JARs) no classpath,
    removendo duplicatas mantendo a ordem original.
    """
    resolved = []

    for cp_string in cp_inputs:
        # Suporta tanto múltiplos parâmetros do Click quanto separadores nativos (: ou ;)
        for pattern in cp_string.split(os.pathsep):
            if "**" in pattern or "*" in pattern:
                matches = glob.glob(pattern, recursive=True)
                for match in matches:
                    p = Path(match)
                    if p.is_dir() or (p.is_file() and p.suffix == ".jar"):
                        resolved.append(str(p.resolve()))
            else:
                p = Path(pattern)
                # Agora aceita pastas (como 'src' e 'bin') E arquivos .jar
                if p.is_dir() or (p.is_file() and p.suffix == ".jar"):
                    resolved.append(str(p.resolve()))
                else:
                    raise click.BadParameter(
                        f"Caminho inválido ou não encontrado (deve ser pasta ou .jar): {pattern}"
                    )

    if not resolved:
        raise click.BadParameter("Nenhum diretório ou arquivo .jar válido foi resolvido para o classpath.")

    # Remove duplicatas mantendo a ordem de inserção (importante para a precedência do Java)
    unique_resolved = list(dict.fromkeys(resolved))

    return os.pathsep.join(unique_resolved)


@click.command()
@click.option("--java-bin", required=False, default=None)
@click.option("--main-class", required=True)
# Alterado para --class-path, definido como multiplo e help atualizado
@click.option(
    "--class-path",
    multiple=True,
    required=True,
    help="Aceita pastas, JARs ou padrões glob (ex: /libs/**/*.jar). Pode ser usado várias vezes."
)
@click.option("--java-opt", multiple=True)
@click.option("--simulation-args", default="")
@click.option("--repeat", default=1, type=int)
@click.option("--threads", default=max(1, os.cpu_count() or 1), type=int)
@click.option("--timeout", default=None, type=int)
@click.option("--output", required=True, type=click.Path(path_type=Path))
@click.option("--logs", required=True, type=click.Path(path_type=Path))
@click.option("--csv-output", required=True, type=click.Path(path_type=Path))
@click.option("--regex-file", required=True, type=click.Path(exists=True, path_type=Path),
              help="Arquivo com padrões regex.")
@click.option("--group-by", multiple=True, required=True, help="Colunas para agrupar no ODS.")
@click.option("--calc-col", required=True, help="Coluna numérica para aplicar as fórmulas no ODS.")
def main(
        java_bin, main_class, class_path, java_opt, simulation_args,
        repeat, threads, timeout, output, logs, csv_output,
        regex_file, group_by, calc_col,
):
    java = java_bin or JavaRunner.resolve_java()
    # repassa a tupla de classpaths capturados pelo click
    resolved_cp = resolve_classpath(class_path)
    patterns = DataEngine.load_patterns(regex_file)

    runner = JavaRunner(
        java_bin=java,
        classpath=resolved_cp,
        main_class=main_class,
        java_opts=list(java_opt),
        timeout_s=timeout,
    )

    executor = ParallelExecutor(runner=runner, parallelism=threads, log_directory=logs)
    parsed_args = shlex.split(simulation_args)
    results = executor.execute(repeat=repeat, simulation_args=parsed_args)

    failed = [item for item in results if item.failed]
    if failed:
        click.echo("Simulações com falha:")
        for item in failed:
            click.echo(f"Simulação {item.simulation_id}: retorno {item.return_code}")

    events = []
    for result in results:
        if result.failed:
            continue
        parsed = DataEngine.parse_log(result.stdout, result.simulation_id, patterns)
        events.extend(parsed)

    if not events:
        click.echo("Nenhum evento capturado. Verifique suas Regexes.")
        return

    # Descobrir todos os cabeçalhos para o CSV dinamicamente
    headers = []
    for event in events:
        for k in event.keys():
            if k not in headers:
                headers.append(k)

    csv_output.parent.mkdir(parents=True, exist_ok=True)
    with csv_output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(events)

    report = OdsReport(events, group_by=list(group_by), calc_col=calc_col)
    output.parent.mkdir(parents=True, exist_ok=True)
    report.save(output)

    click.echo(f"ODS gerado em: {output}")
    click.echo(f"CSV gerado em: {csv_output}")


if __name__ == "__main__":
    main()