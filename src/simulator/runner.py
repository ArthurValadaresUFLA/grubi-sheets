from __future__ import annotations

import concurrent.futures
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(slots=True)
class SimulationResult:
    simulation_id: int
    stdout: str
    return_code: int
    failed: bool
    command: list[str]


class JavaRunner:
    def __init__(
        self,
        java_bin: str,
        classpath: str,
        main_class: str,
        java_opts: list[str] | None = None,
        timeout_s: int | None = None,
    ):
        self.java_bin = java_bin
        self.classpath = classpath
        self.main_class = main_class
        self.java_opts = java_opts or []
        self.timeout_s = timeout_s

    @classmethod
    def resolve_java(cls) -> str:
        java_home = os.environ.get("JAVA_HOME")

        if java_home:
            candidate = Path(java_home) / "bin" / "java"
            if candidate.exists():
                return str(candidate)

        java = shutil.which("java")

        if java:
            return java

        raise RuntimeError("Java não encontrado")

    def build_command(self, simulation_args: Sequence[str]) -> list[str]:
        return [
            self.java_bin,
            *self.java_opts,
            "-classpath",
            self.classpath,
            self.main_class,
            *simulation_args,
        ]

    def run_single(
        self,
        simulation_id: int,
        simulation_args: Sequence[str],
    ) -> SimulationResult:
        cmd = self.build_command(simulation_args)

        try:
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_s,
                check=False,
            )

            return SimulationResult(
                simulation_id=simulation_id,
                stdout=process.stdout,
                return_code=process.returncode,
                failed=process.returncode != 0,
                command=cmd,
            )

        except subprocess.TimeoutExpired as exc:
            return SimulationResult(
                simulation_id=simulation_id,
                stdout=str(exc),
                return_code=-1,
                failed=True,
                command=cmd,
            )


class ParallelExecutor:
    def __init__(
        self,
        runner: JavaRunner,
        parallelism: int,
        log_directory: Path,
    ):
        self.runner = runner
        self.parallelism = parallelism
        self.log_directory = log_directory

    def execute(
        self,
        repeat: int,
        simulation_args: Sequence[str],
    ) -> list[SimulationResult]:
        self.log_directory.mkdir(parents=True, exist_ok=True)

        results: list[SimulationResult] = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(self.parallelism, repeat)
        ) as executor:
            futures = {
                executor.submit(
                    self.runner.run_single,
                    sim_id,
                    simulation_args,
                ): sim_id
                for sim_id in range(1, repeat + 1)
            }

            for future in concurrent.futures.as_completed(futures):
                result = future.result()

                log_file = (
                    self.log_directory
                    / f"sim_{result.simulation_id:04d}.log"
                )

                log_file.write_text(
                    result.stdout,
                    encoding="utf-8",
                    errors="replace",
                )

                results.append(result)

        results.sort(key=lambda item: item.simulation_id)

        return results