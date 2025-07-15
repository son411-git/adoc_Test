import os
import re

def extract_tagged_region(lines, tag_name):
    """Extract lines inside a specific tag region (excluding tag comments)."""
    start_tag = f"// tag::{tag_name}[]"
    end_tag = f"// end::{tag_name}[]"
    extracted, inside = [], False

    for line in lines:
        if start_tag in line:
            inside = True
            continue
        if end_tag in line:
            inside = False
            continue
        if inside:
            extracted.append(line)
    return extracted

def should_exclude_comment(line):
    """Detect tag comments that should be removed from final output."""
    stripped = line.strip()
    return stripped.startswith("// tag::") or stripped.startswith("// end::")

def merge_lines(lines, base_dir):
    """Process lines with recursive include resolution."""
    include_pattern = re.compile(r'\binclude::([^\[]+)\[([^\]]*)\]')
    merged_lines = []

    for line in lines:
        stripped = line.strip()

        # 주석은 그대로 유지하되 tag:: 주석은 제거
        if stripped.startswith('//'):
            if should_exclude_comment(line):
                continue
            merged_lines.append(line)
            continue

        match = include_pattern.search(line)
        if match:
            include_path = match.group(1).strip()
            options = match.group(2).strip()
            resolved_path = os.path.normpath(os.path.join(base_dir, include_path))

            if not os.path.exists(resolved_path):
                print(f'❌ 파일 없음: {resolved_path}')
                merged_lines.append(line)
                continue

            print(f'📥 포함 중: {resolved_path}')
            with open(resolved_path, 'r', encoding='utf-8') as f:
                included_lines = f.readlines()

            # tag 처리 여부 확인
            tag_match = re.search(r'tag=([\w\-]+)', options)
            if tag_match:
                tag_name = tag_match.group(1)
                tagged = extract_tagged_region(included_lines, tag_name)
                nested = merge_lines(tagged, os.path.dirname(resolved_path))
            else:
                nested = merge_lines(included_lines, os.path.dirname(resolved_path))

            merged_lines.extend(nested)
        else:
            if should_exclude_comment(line):
                continue
            merged_lines.append(line)

    return merged_lines

def merge_adoc(entry_file, output_file):
    with open(entry_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    base_dir = os.path.dirname(entry_file)
    final = merge_lines(lines, base_dir)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(final)

    print(f'✅ 병합 완료: {output_file}')

# 실행 예시
if __name__ == "__main__":
    merge_adoc("index.adoc", "merged.adoc")