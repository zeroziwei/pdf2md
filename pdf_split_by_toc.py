"""
PDF目录切分工具
根据PDF目录/大纲将PDF切分为多个独立的文件
"""

import fitz  # PyMuPDF
import os
import re
from pathlib import Path


def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    # 移除或替换非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    filename = re.sub(illegal_chars, "_", filename)
    # 移除前后空格
    filename = filename.strip()
    # 限制长度
    if len(filename) > 100:
        filename = filename[:100]
    return filename


def split_pdf_by_toc(pdf_path, output_dir=None, create_chapters=True):
    """
    根据目录切分PDF

    参数:
        pdf_path: PDF文件路径
        output_dir: 输出目录（默认为 PDF文件名_chapters）
        create_chapters: 是否创建章节文件夹
    """
    try:
        # 打开PDF
        doc = fitz.open(pdf_path)
        toc = doc.get_toc()

        if not toc:
            print("错误: 此PDF没有目录信息，无法自动切分")
            doc.close()
            return False

        # 设置输出目录
        if output_dir is None:
            pdf_name = Path(pdf_path).stem
            output_dir = f"{pdf_name}_chapters"

        os.makedirs(output_dir, exist_ok=True)

        print(f"PDF文件: {Path(pdf_path).name}")
        print(f"总页数: {doc.page_count}")
        print(f"目录项数: {len(toc)}")
        print(f"输出目录: {output_dir}\n")

        # 分析目录结构，找出一级章节
        chapters = []
        for i, (level, title, start_page) in enumerate(toc):
            # 只处理一级标题（level == 1）
            if level == 1:
                # 确定结束页
                end_page = None
                # 找下一个同级或更高级的标题
                for j in range(i + 1, len(toc)):
                    next_level, next_title, next_page = toc[j]
                    if next_level <= level:
                        end_page = next_page - 1
                        break

                # 如果没有找到，使用PDF末尾
                if end_page is None:
                    end_page = doc.page_count

                chapters.append(
                    {
                        "title": title,
                        "start": start_page,
                        "end": end_page,
                        "level": level,
                    }
                )

        print(f"找到 {len(chapters)} 个主要章节\n")
        print("=" * 80)

        # 切分并保存每个章节
        for idx, chapter in enumerate(chapters, 1):
            title = chapter["title"]
            start = chapter["start"] - 1  # PyMuPDF使用0-based索引
            end = chapter["end"] - 1

            # 生成安全的文件名
            safe_title = sanitize_filename(title)
            output_filename = f"{idx:02d}_{safe_title}.pdf"
            output_path = os.path.join(output_dir, output_filename)

            # 创建新PDF并复制页面
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=start, to_page=end)

            # 保存
            new_doc.save(output_path)
            new_doc.close()

            page_count = end - start + 1
            print(f"[{idx}/{len(chapters)}] {title}")
            print(f"     页面: {chapter['start']}-{chapter['end']} (共{page_count}页)")
            print(f"     保存为: {output_filename}")
            print()

        doc.close()

        print("=" * 80)
        print(f"✅ 切分完成！共生成 {len(chapters)} 个文件")
        print(f"📁 输出目录: {os.path.abspath(output_dir)}")

        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback

        traceback.print_exc()
        return False


def split_pdf_by_level(pdf_path, output_dir=None, split_level=1):
    """
    根据指定层级的目录切分PDF

    参数:
        pdf_path: PDF文件路径
        output_dir: 输出目录
        split_level: 按哪个层级切分（1=一级标题，2=二级标题，等）
    """
    try:
        doc = fitz.open(pdf_path)
        toc = doc.get_toc()

        if not toc:
            print("错误: 此PDF没有目录信息")
            doc.close()
            return False

        if output_dir is None:
            pdf_name = Path(pdf_path).stem
            output_dir = f"{pdf_name}_split_level{split_level}"

        os.makedirs(output_dir, exist_ok=True)

        print(f"按 {split_level} 级目录切分")
        print(f"输出目录: {output_dir}\n")

        # 筛选指定级别的目录项
        sections = []
        for i, (level, title, start_page) in enumerate(toc):
            if level == split_level:
                # 找结束页
                end_page = doc.page_count
                for j in range(i + 1, len(toc)):
                    next_level, _, next_page = toc[j]
                    if next_level <= split_level:
                        end_page = next_page - 1
                        break

                sections.append({"title": title, "start": start_page, "end": end_page})

        print(f"找到 {len(sections)} 个{split_level}级章节\n")

        # 保存每个章节
        for idx, section in enumerate(sections, 1):
            safe_title = sanitize_filename(section["title"])
            output_filename = f"{idx:02d}_{safe_title}.pdf"
            output_path = os.path.join(output_dir, output_filename)

            new_doc = fitz.open()
            new_doc.insert_pdf(
                doc, from_page=section["start"] - 1, to_page=section["end"] - 1
            )
            new_doc.save(output_path)
            new_doc.close()

            page_count = section["end"] - section["start"] + 1
            print(
                f"[{idx}/{len(sections)}] {section['title']} (页{section['start']}-{section['end']}, 共{page_count}页)"
            )

        doc.close()
        print(f"\n✅ 完成！共生成 {len(sections)} 个文件")
        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def main():
    """主函数"""
    import sys

    print("=" * 80)
    print("                     PDF目录切分工具")
    print("=" * 80)
    print()

    if len(sys.argv) < 2:
        # 查找当前目录的PDF文件
        import glob

        pdf_files = glob.glob("*.pdf")

        if not pdf_files:
            print("用法:")
            print("  python pdf_split_by_toc.py <PDF文件路径> [输出目录]")
            print()
            print("或者将脚本放在包含PDF的目录中直接运行")
            return

        print(f"找到 {len(pdf_files)} 个PDF文件:")
        for i, pdf in enumerate(pdf_files, 1):
            print(f"  {i}. {pdf}")
        print()

        if len(pdf_files) == 1:
            pdf_path = pdf_files[0]
            print(f"自动选择: {pdf_path}\n")
        else:
            choice = input("请选择要处理的文件编号（直接回车选择第一个）: ").strip()
            if not choice:
                pdf_path = pdf_files[0]
            else:
                try:
                    idx = int(choice) - 1
                    pdf_path = pdf_files[idx]
                except (ValueError, IndexError):
                    print("无效的选择")
                    return
    else:
        pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"错误: 文件不存在: {pdf_path}")
        return

    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    # 询问切分方式
    print("\n切分方式:")
    print("  1. 按一级目录切分（章节）- 推荐")
    print("  2. 按二级目录切分（小节）")
    print("  3. 自定义级别")

    mode = input("\n请选择 (1-3，直接回车使用默认): ").strip()

    if not mode or mode == "1":
        split_pdf_by_toc(pdf_path, output_dir)
    elif mode == "2":
        split_pdf_by_level(pdf_path, output_dir, split_level=2)
    elif mode == "3":
        level = input("请输入目录级别 (1, 2, 3...): ").strip()
        try:
            level = int(level)
            split_pdf_by_level(pdf_path, output_dir, split_level=level)
        except ValueError:
            print("无效的级别")


if __name__ == "__main__":
    main()
