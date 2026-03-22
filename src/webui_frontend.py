# -*- coding: utf-8 -*-
"""
WebUI frontend asset preparation & build helper.
"""
from __future__ import annotations
import logging
import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Sequence
from datetime import datetime

# 导入涨停分组数据获取函数
try:
    from src.storage import get_group_stocks, get_self_select_stocks
    from src.analyzer import get_stock_name_multi_source
except ImportError:
    get_group_stocks = None
    get_self_select_stocks = None
    get_stock_name_multi_source = None

logger = logging.getLogger(__name__)
_FALSEY_ENV_VALUES = {"0", "false", "no", "off"}
_BUILD_INPUT_FILES = (
    "package.json", "package-lock.json", "vite.config.ts", "tsconfig.json",
    "tsconfig.app.json", "tsconfig.node.json", "eslint.config.js",
    "postcss.config.js", "tailwind.config.js", "index.html",
)
_BUILD_INPUT_DIRS = ("src", "public")

def _is_truthy_env(var_name: str, default: str = "true") -> bool:
    value = os.getenv(var_name, default).strip().lower()
    return value not in _FALSEY_ENV_VALUES

def _safe_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0

def _tree_latest_mtime(root: Path) -> float:
    if not root.exists():
        return 0.0
    latest = 0.0
    try:
        for p in root.rglob("*"):
            if p.is_file():
                latest = max(latest, _safe_mtime(p))
    except OSError:
        latest = max(latest, _safe_mtime(root))
    return latest

def _max_mtime(paths: Iterable[Path]) -> float:
    latest = 0.0
    for path in paths:
        latest = max(latest, _safe_mtime(path))
    return latest

def _resolve_artifact_index(frontend_dir: Path) -> Path:
    static_index = (frontend_dir / ".." / ".." / "static" / "index.html").resolve()
    dist_index = frontend_dir / "dist" / "index.html"
    build_index = frontend_dir / "build" / "index.html"
    if static_index.exists():
        return static_index
    fallback_candidates = [p for p in (dist_index, build_index) if p.exists()]
    return max(fallback_candidates, key=_safe_mtime) if fallback_candidates else static_index

def _needs_dependency_install(frontend_dir: Path, package_json: Path, lock_file: Path, force_build: bool) -> bool:
    node_modules_dir = frontend_dir / "node_modules"
    install_marker = node_modules_dir / ".package-lock.json"
    deps_marker_mtime = _safe_mtime(install_marker) if install_marker.exists() else _safe_mtime(node_modules_dir)
    deps_input_mtime = _max_mtime((package_json, lock_file))
    return force_build or not node_modules_dir.exists() or deps_marker_mtime < deps_input_mtime

def _collect_build_inputs_latest_mtime(frontend_dir: Path) -> float:
    latest = _max_mtime(frontend_dir / filename for filename in _BUILD_INPUT_FILES)
    for dirname in _BUILD_INPUT_DIRS:
        latest = max(latest, _tree_latest_mtime(frontend_dir / dirname))
    return latest

def _needs_frontend_build(frontend_dir: Path, force_build: bool) -> tuple[bool, Path]:
    artifact_index = _resolve_artifact_index(frontend_dir)
    inputs_latest_mtime = _collect_build_inputs_latest_mtime(frontend_dir)
    artifact_mtime = _safe_mtime(artifact_index)
    needs_build = force_build or not artifact_index.exists() or artifact_mtime < inputs_latest_mtime
    return needs_build, artifact_index

def _run_frontend_commands(commands: Sequence[Sequence[str]], frontend_dir: Path) -> bool:
    try:
        for command in commands:
            logger.info("执行前端构建命令: %s", " ".join(command))
            subprocess.run(command, cwd=frontend_dir, check=True, capture_output=True)
        logger.info("前端静态资源编译构建完成")
        return True
    except subprocess.CalledProcessError as exc:
        logger.error("前端命令执行失败: %s", " ".join(exc.cmd))
        return False

def _convert_stock_code_to_info(stock_code: str) -> dict:
    """将股票代码转换为包含code和name的对象"""
    if not stock_code:
        return {"code": "", "name": ""}
    try:
        if get_stock_name_multi_source:
            name = get_stock_name_multi_source(stock_code)
            if name and not name.startswith('股票'):
                return {"code": stock_code, "name": name}
    except Exception:
        pass
    return {"code": stock_code, "name": stock_code}


# 修复：涨停分组数据同步，路径和页面fetch完全一致
def sync_limit_group_static_data() -> bool:
    if get_group_stocks is None or get_self_select_stocks is None:
        logger.debug("涨停分组数据模块未初始化，跳过数据同步")
        return False
    try:
        # 修复：数据路径和页面fetch的/strategy/limit_group_data.json完全一致
        static_data_dir = Path(__file__).resolve().parent.parent / "static" / "strategy"
        static_data_dir.mkdir(parents=True, exist_ok=True)
        data_file_path = static_data_dir / "limit_group_data.json"

        # 获取盘后分组数据（股票代码列表）
        first_codes = get_group_stocks("首板涨停组") or []
        second_codes = get_group_stocks("两板涨停组") or []
        self_select_codes = get_self_select_stocks() or []

        # 转换为包含code和name的对象列表
        first_limit_group = [_convert_stock_code_to_info(code) for code in first_codes]
        second_limit_group = [_convert_stock_code_to_info(code) for code in second_codes]
        self_select_stocks = [_convert_stock_code_to_info(code) for code in self_select_codes]

        # 组装数据，和前端类型完全匹配
        sync_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "update_date": datetime.now().strftime("%Y-%m-%d"),
            "first_limit_group": first_limit_group,
            "second_limit_group": second_limit_group,
            "self_select_stocks": self_select_stocks,
            "source": "盘后统一入组数据"
        }

        # 写入文件
        with open(data_file_path, "w", encoding="utf-8") as f:
            json.dump(sync_data, f, ensure_ascii=False, indent=2)

        logger.info("✅ 涨停分组数据同步完成 | 首板:%d只 两板:%d只 自选:%d只", len(first_limit_group), len(second_limit_group), len(self_select_stocks))
        return True
    except Exception as e:
        logger.debug("涨停分组数据同步失败: %s", str(e))
        return False

# 主入口函数
def prepare_webui_frontend_assets() -> bool:
    frontend_dir = Path(__file__).resolve().parent.parent / "apps" / "dsa-web"
    auto_build_enabled = _is_truthy_env("WEBUI_AUTO_BUILD", "true")
    artifact_index = _resolve_artifact_index(frontend_dir)

    # 非自动构建模式，仅同步数据
    if not auto_build_enabled:
        if artifact_index.exists():
            logger.info("WEBUI_AUTO_BUILD=false，使用已编译静态资源")
            sync_limit_group_static_data()
            return True
        logger.warning("未检测到前端静态资源，且自动构建已关闭")
        return False

    # 检查前端项目
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        logger.warning("前端项目目录不存在，跳过构建")
        return False

    # 检查npm环境
    npm_path = shutil.which("npm")
    if not npm_path:
        logger.warning("未检测到npm环境，无法构建前端")
        return False

    force_build = _is_truthy_env("WEBUI_FORCE_BUILD", "false")
    lock_file = frontend_dir / "package-lock.json"

    # 判断构建需求
    needs_install = _needs_dependency_install(frontend_dir, package_json, lock_file, force_build)
    needs_build, _ = _needs_frontend_build(frontend_dir, force_build)

    # 资源最新，仅同步数据
    if not needs_install and not needs_build:
        logger.info("前端静态资源已是最新，同步涨停分组数据")
        sync_limit_group_static_data()
        return True

    # 组装构建命令
    commands = []
    if needs_install:
        commands.append([npm_path, "ci" if lock_file.exists() else "install"])
    if needs_build:
        commands.append([npm_path, "run", "build"])

    # 执行构建
    build_success = _run_frontend_commands(commands, frontend_dir)
    if build_success:
        sync_limit_group_static_data()

    return build_success