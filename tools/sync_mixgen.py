from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DESTINATION = Path(r'C:\Users\felip\OneDrive\git_work\mixgen')
ROBOCOPY_SUCCESS_MAX_EXIT_CODE = 7
DEFAULT_EXCLUDE_DIRS = [
    '.git',
    '.mypy_cache',
    '.pytest_cache',
    '.ruff_cache',
    '.streamlit',
    '__pycache__',
    'Backup',
    'venv',
    '.venv',
]
DEFAULT_EXCLUDE_FILES = [
    '*.pyc',
    '*.pyo',
    '*.zip',
    '*.7z',
    '*.rar',
    '.DS_Store',
    'Thumbs.db',
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Sincroniza mudanças do projeto atual para o espelho mixgen usando robocopy.',
    )
    parser.add_argument(
        '--source',
        type=Path,
        default=PROJECT_ROOT,
        help=f'Diretório de origem. Padrão: {PROJECT_ROOT}',
    )
    parser.add_argument(
        '--destination',
        type=Path,
        default=DEFAULT_DESTINATION,
        help=f'Diretório de destino. Padrão: {DEFAULT_DESTINATION}',
    )
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Mantém o script rodando e sincroniza em intervalos regulares.',
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='Intervalo em segundos entre sincronizações no modo --watch. Padrão: 10.',
    )
    parser.add_argument(
        '--include-backup',
        action='store_true',
        help='Inclui a pasta Backup na sincronização.',
    )
    parser.add_argument(
        '--include-venv',
        action='store_true',
        help='Inclui venv/.venv na sincronização. Normalmente não recomendado.',
    )
    parser.add_argument(
        '--include-archives',
        action='store_true',
        help='Inclui arquivos compactados, como .zip, .7z e .rar. Normalmente não recomendado para o espelho git.',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Mostra o que seria copiado, sem alterar o destino.',
    )
    return parser.parse_args()


def validate_paths(source: Path, destination: Path) -> tuple[Path, Path]:
    source = source.resolve()
    destination = destination.resolve()

    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f'Diretório de origem não encontrado: {source}')
    if not destination.exists() or not destination.is_dir():
        raise FileNotFoundError(f'Diretório de destino não encontrado: {destination}')
    if source == destination:
        raise ValueError('Origem e destino não podem ser o mesmo diretório.')

    return source, destination


def build_exclude_dirs(include_backup: bool, include_venv: bool) -> list[str]:
    excluded = list(DEFAULT_EXCLUDE_DIRS)
    # if include_backup:
    #     excluded = [item for item in excluded if item != 'Backup']
    if include_venv:
        excluded = [item for item in excluded if item not in {'venv', '.venv'}]
    return excluded


def build_robocopy_command(args: argparse.Namespace) -> list[str]:
    source, destination = validate_paths(args.source, args.destination)
    exclude_dirs = build_exclude_dirs(args.include_backup, args.include_venv)
    exclude_files = [] if args.include_archives else list(DEFAULT_EXCLUDE_FILES)

    command = [
        'robocopy',
        str(source),
        str(destination),
        '/E',
        '/COPY:DAT',
        '/DCOPY:DAT',
        '/XO',
        '/FFT',
        '/R:2',
        '/W:2',
        '/NP',
        '/MT:8',
    ]

    if args.dry_run:
        command.append('/L')

    if exclude_dirs:
        command.extend(['/XD', *exclude_dirs])
    if exclude_files:
        command.extend(['/XF', *exclude_files])

    return command


def run_robocopy(args: argparse.Namespace) -> int:
    if shutil.which('robocopy') is None:
        raise RuntimeError('robocopy não foi encontrado no PATH. Este script precisa rodar no Windows.')

    command = build_robocopy_command(args)
    print(f'\nSincronizando: {args.source} -> {args.destination}')
    print('Modo:', 'simulação' if args.dry_run else 'cópia real')

    completed = subprocess.run(command, check=False)
    code = completed.returncode
    if code > ROBOCOPY_SUCCESS_MAX_EXIT_CODE:
        raise RuntimeError(f'robocopy falhou com código {code}.')

    print(f'robocopy finalizado com código {code}.')
    return code


def run_watch(args: argparse.Namespace) -> None:
    interval = max(3, int(args.interval))
    print(f'Monitorando mudanças a cada {interval}s. Use Ctrl+C para parar.')

    while True:
        try:
            run_robocopy(args)
        except RuntimeError as exc:
            print(f'Erro de sincronização: {exc}', file=sys.stderr)
        time.sleep(interval)


def main() -> int:
    args = parse_args()

    try:
        if args.watch:
            run_watch(args)
        else:
            run_robocopy(args)
    except KeyboardInterrupt:
        print('\nSincronização interrompida pelo usuário.')
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f'Erro: {exc}', file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
