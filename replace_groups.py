import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


# ==================== 配置区域 ====================

# 需要处理的文件夹路径
FOLDER_PATH = "/Users/xiaomo/Code/Individual/maa-working-schedule/333/333-all-lmd"

# 公共 groups 配置文件名
GROUPS_FILE_NAME = "config.json"

# 是否在替换前生成备份
CREATE_BACKUP = True

# 备份文件夹名称
BACKUP_FOLDER_NAME = "backups"

# 是否递归处理子文件夹
RECURSIVE = False

# JSON 缩进空格数
INDENT_SIZE = 4

# 需要完全展开的对象字段
EXPANDED_OBJECT_FIELDS = {
    "Fiammetta",
    "drones",
    "scheduleType"
}

# ================================================


def read_json(file_path: Path) -> Any:
    """读取 JSON 文件。"""
    with file_path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def compact_json(value: Any) -> str:
    """
    将值转换为单行 JSON。

    输出示例：
    {"name":"test","operators":["A","B"]}
    """
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":")
    )


def readable_compact_json(value: Any) -> str:
    """
    将值转换为单行 JSON，并在逗号和冒号后保留空格。

    主要用于 period：

    ["21:01", "23:59"]
    """
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(", ", ": ")
    )


def is_scalar(value: Any) -> bool:
    """判断是否为 JSON 基础类型。"""
    return (
        value is None
        or isinstance(value, (str, int, float, bool))
    )


def is_scalar_array(value: Any) -> bool:
    """判断是否为仅包含基础值的一维数组。"""
    return (
        isinstance(value, list)
        and all(is_scalar(item) for item in value)
    )


def is_scalar_matrix(value: Any) -> bool:
    """判断是否为仅包含基础值的二维数组。"""
    return (
        isinstance(value, list)
        and all(
            isinstance(item, list)
            and all(is_scalar(child) for child in item)
            for item in value
        )
    )


def is_object_array(value: Any) -> bool:
    """判断数组是否包含对象。"""
    return (
        isinstance(value, list)
        and any(isinstance(item, dict) for item in value)
    )


def format_expanded_object(
    value: dict[str, Any],
    indent_level: int
) -> str:
    """
    完全展开对象。

    效果：

    "drones":{
        "room":"manufacture",
        "index":1,
        "enable":true,
        "order":"pre"
    }
    """
    if not value:
        return "{}"

    indent = " " * indent_level
    child_indent = " " * (
        indent_level + INDENT_SIZE
    )

    lines: list[str] = []

    for key, child in value.items():
        key_text = compact_json(key)
        child_text = format_json(
            child,
            indent_level + INDENT_SIZE,
            key_name=key
        )

        lines.append(
            f"{child_indent}{key_text}:{child_text}"
        )

    return (
        "{\n"
        + ",\n".join(lines)
        + "\n"
        + indent
        + "}"
    )


def format_operator_object(
    value: dict[str, Any],
    indent_level: int
) -> str:
    """
    格式化包含 operators 字段的对象。

    效果：

    {"use_operator_groups":true,"product":"LMD","sort":true,
        "operators":["trade-0-LMD-main"]
    }
    """
    indent = " " * indent_level
    field_indent = " " * (
        indent_level + INDENT_SIZE
    )

    normal_fields: list[str] = []

    for key, child in value.items():
        if key == "operators":
            continue

        normal_fields.append(
            f"{compact_json(key)}:{compact_json(child)}"
        )

    operators_text = compact_json(
        value["operators"]
    )

    if normal_fields:
        first_line = (
            "{"
            + ",".join(normal_fields)
            + ","
        )
    else:
        first_line = "{"

    return (
        first_line
        + "\n"
        + field_indent
        + f'"operators":{operators_text}'
        + "\n"
        + indent
        + "}"
    )


def format_object(
    value: dict[str, Any],
    indent_level: int,
    key_name: str | None = None
) -> str:
    """格式化 JSON 对象。"""
    if not value:
        return "{}"

    # Fiammetta、drones 字段完全展开
    if key_name in EXPANDED_OBJECT_FIELDS:
        return format_expanded_object(
            value,
            indent_level
        )

    # operators 字段始终单独一行
    if "operators" in value:
        return format_operator_object(
            value,
            indent_level
        )

    # 对象中不存在复杂对象或对象数组时，保持单行
    has_complex_value = any(
        isinstance(child, dict)
        or is_object_array(child)
        for child in value.values()
    )

    if not has_complex_value:
        return compact_json(value)

    indent = " " * indent_level
    child_indent = " " * (
        indent_level + INDENT_SIZE
    )

    lines: list[str] = []

    for key, child in value.items():
        key_text = compact_json(key)
        child_text = format_json(
            child,
            indent_level + INDENT_SIZE,
            key_name=key
        )

        lines.append(
            f"{child_indent}{key_text}:{child_text}"
        )

    return (
        "{\n"
        + ",\n".join(lines)
        + "\n"
        + indent
        + "}"
    )


def format_period_array(
    value: list[Any],
    indent_level: int
) -> str:
    """
    格式化 period 字段。

    只展开外层数组，内部时间段数组保持单行。

    效果：

    "period": [
        ["21:01", "23:59"],
        ["00:00", "5:00"]
    ]
    """
    if not value:
        return "[]"

    indent = " " * indent_level
    child_indent = " " * (
        indent_level + INDENT_SIZE
    )

    lines: list[str] = []

    for item in value:
        if isinstance(item, list):
            item_text = readable_compact_json(item)
        else:
            item_text = format_json(
                item,
                indent_level + INDENT_SIZE
            )

        lines.append(
            child_indent + item_text
        )

    return (
        "[\n"
        + ",\n".join(lines)
        + "\n"
        + indent
        + "]"
    )


def format_array(
    value: list[Any],
    indent_level: int,
    key_name: str | None
) -> str:
    """格式化 JSON 数组。"""
    if not value:
        return "[]"

    # period 只展开外层数组
    if key_name == "period":
        return format_period_array(
            value,
            indent_level
        )

    # 普通基础值数组保持单行
    if is_scalar_array(value):
        return compact_json(value)

    # 普通二维基础值数组保持单行
    if is_scalar_matrix(value):
        return compact_json(value)

    indent = " " * indent_level
    child_indent = " " * (
        indent_level + INDENT_SIZE
    )

    lines: list[str] = []

    for item in value:
        if isinstance(item, dict):
            item_text = format_object(
                item,
                indent_level + INDENT_SIZE
            )
        else:
            item_text = format_json(
                item,
                indent_level + INDENT_SIZE
            )

        lines.append(
            child_indent + item_text
        )

    return (
        "[\n"
        + ",\n".join(lines)
        + "\n"
        + indent
        + "]"
    )


def format_json(
    value: Any,
    indent_level: int = 0,
    key_name: str | None = None
) -> str:
    """
    自定义格式化 JSON。

    规则：

    1. 基础值直接输出。
    2. 基础值数组保持单行。
    3. 对象数组展开数组。
    4. 数组内的普通对象尽量单行。
    5. 对象中的 operators 字段单独一行。
    6. period 只展开外层数组。
    7. Fiammetta 和 drones 对象完全展开。
    """
    if is_scalar(value):
        return compact_json(value)

    if isinstance(value, list):
        return format_array(
            value,
            indent_level,
            key_name
        )

    if isinstance(value, dict):
        return format_object(
            value,
            indent_level,
            key_name
        )

    raise TypeError(
        f"不支持的数据类型：{type(value).__name__}"
    )


def write_json(
    file_path: Path,
    data: Any
) -> None:
    """以自定义格式写入 JSON 文件。"""
    content = format_json(data)

    file_path.write_text(
        content + "\n",
        encoding="utf-8"
    )


def create_backup(
    source_file: Path,
    backup_folder: Path,
    timestamp: str
) -> None:
    """
    创建备份文件。

    示例：

    schedule.json
    -> backups/schedule-20260711-120000.json.bak
    """
    backup_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    backup_name = (
        f"{source_file.stem}-"
        f"{timestamp}"
        f"{source_file.suffix}.bak"
    )

    shutil.copy2(
        source_file,
        backup_folder / backup_name
    )


def replace_all_groups(
    value: Any,
    groups: list[Any]
) -> int:
    """
    递归替换任意层级中的 groups 字段。

    返回替换次数。
    """
    replaced_count = 0

    if isinstance(value, dict):
        for key in list(value.keys()):
            if key == "groups":
                value[key] = groups
                replaced_count += 1
            else:
                replaced_count += replace_all_groups(
                    value[key],
                    groups
                )

    elif isinstance(value, list):
        for item in value:
            replaced_count += replace_all_groups(
                item,
                groups
            )

    return replaced_count


def get_json_files(
    folder: Path
) -> list[Path]:
    """获取需要处理的 JSON 文件。"""
    if RECURSIVE:
        files = folder.rglob("*.json")
    else:
        files = folder.glob("*.json")

    return sorted(files)


def main() -> None:
    folder = (
        Path(FOLDER_PATH)
        .expanduser()
        .resolve()
    )

    if not folder.is_dir():
        raise NotADirectoryError(
            f"文件夹不存在：{folder}"
        )

    groups_file = folder / GROUPS_FILE_NAME

    if not groups_file.is_file():
        raise FileNotFoundError(
            f"未找到配置文件：{groups_file}"
        )

    groups_data = read_json(groups_file)

    if not isinstance(groups_data, dict):
        raise ValueError(
            f"{GROUPS_FILE_NAME} 的根节点必须是对象"
        )

    groups = groups_data.get("groups")

    if not isinstance(groups, list):
        raise TypeError(
            f'{GROUPS_FILE_NAME} 中的 '
            '"groups" 字段必须是数组'
        )

    backup_folder = (
        folder / BACKUP_FOLDER_NAME
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )

    updated_file_count = 0
    replaced_field_count = 0

    for json_file in get_json_files(folder):
        # 跳过公共配置文件
        if (
            json_file.resolve()
            == groups_file.resolve()
        ):
            continue

        # 递归处理时跳过备份文件夹
        if backup_folder in json_file.parents:
            continue

        data = read_json(json_file)

        replaced_count = replace_all_groups(
            data,
            groups
        )

        if replaced_count == 0:
            continue

        if CREATE_BACKUP:
            create_backup(
                source_file=json_file,
                backup_folder=backup_folder,
                timestamp=timestamp
            )

        write_json(
            json_file,
            data
        )

        updated_file_count += 1
        replaced_field_count += replaced_count

    print(
        f"已更新 {updated_file_count} 个文件，"
        f"替换 {replaced_field_count} 个 groups 字段"
    )


if __name__ == "__main__":
    main()