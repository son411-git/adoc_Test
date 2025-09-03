#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET
from tqdm import tqdm

# --- 네임스페이스 상수 지정---
NS = {
    "S100FC":   "http://www.iho.int/S100FC/5.2",
    "S100Base":"http://www.iho.int/S100Base/5.0"
}


# --- <S100FC:alias>값 파싱하는 함수
def extract_acronym(elem):
    if elem is None:
        return ""
    aliases = elem.findall("S100FC:alias", NS)
    texts = [a.text.strip() for a in aliases if a.text]
    short = [t for t in texts if len(t) <= 6]
    if not texts:
        return ""
    if len(texts) == 1:
        return texts[0]
    if len(texts) == 2:
        if len(short) == 2:
            return "/".join(short)
        if len(short) == 1:
            return short[0]
        return ""
    return short[0] if short else ""

# --- <S100FC:valueType> 값 파싱하는 함수 
# code가 featureName이면 C반환 아니면 -> valueType값 반환
def extract_type(attr, is_sub=False):
    if attr is None:
        return "(S)C" if is_sub else "C"
    code = attr.findtext("S100FC:code", namespaces=NS)
    if code == "featureName":
        return "C"
    v = attr.findtext("S100FC:valueType", namespaces=NS) or ""
    v = v.strip()
    if not v:
        return "(S)C" if is_sub else "C"
    if v.isupper():
        return f"(S){v}" if is_sub else v
    if v.lower().startswith("s100_"):
        abbr = ''.join(c for c in v.split("_",1)[1] if c.isupper())
        return f"(S){abbr}" if is_sub else abbr
    return f"(S){v[:2].upper()}" if is_sub else v[:2].upper()

# --- <S100FC:multiplicity> 값 파싱하는 함수
# 1,*
# 0,*
# 1,1 
def get_multiplicity(binding):
    m = binding.find("S100FC:multiplicity", NS)
    if m is None:
        return "0,1"
    low = m.findtext("S100Base:lower", default="0", namespaces=NS).strip()
    up_e = m.find("S100Base:upper", NS)
    if up_e is None:
        up = "1"
    elif up_e.get("infinite") == "true" or up_e.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true":
        up = "*"
    else:
        up = (up_e.text or "1").strip()
    return f"{low},{up}"

# 필수값 반환하는 함수
# 아래 3가지 경우 필수
def is_essential(mult):
    return mult in ("1,1","1,*","2,*")


# 복합속성,단일속성 코드값 반환
def find_attr(root, code, tag):
    return root.find(f".//S100FC:{tag}[S100FC:code='{code}']", NS)

# --- 주어진 ref(속성 코드)에 해당하는 속성(복합/단순) 정보를 AsciiDoc 표 형식의 한 줄로 변환 (재귀적으로 하위 속성까지 처리)
# 복합속성, 단일속성
# 계층 구조 유지하면서 -> asciidoc으로 변환 
def write_binding(ref, root, bind, level=0, with_value_col=False):
    # 복합,단일 속성 노드 찾기
    comp = find_attr(root, ref, "S100_FC_ComplexAttribute")
    simp = find_attr(root, ref, "S100_FC_SimpleAttribute")
    elem = comp if comp is not None else simp

    # 계층 레벨에 따라 들여쓰기 (하위 속성일수록 들여쓰기 증가)
    indent = "\u00A0" * 4 * level
    name = elem.findtext("S100FC:name", default=ref, namespaces=NS).lower() if elem is not None else ref.lower()
    acr  = extract_acronym(elem)
    typ  = extract_type(elem, is_sub=(level>0))
    mult = get_multiplicity(bind) if bind is not None else "0,1"

     # 필수 속성이면 #span:E[]로 감싼다. prefix, 복합 속성이면 bold로 표시
    disp = f"{indent}span:E[{name}]" if is_essential(mult) else f"{indent}{name}"
    if comp is not None:
        disp = f"**{disp}**"


    # Value 컬럼 여부에 따라 표의 열 개수 선택
    if with_value_col:
        line = f"|{disp}|{acr}|{typ}|{mult}| \n"
    else:
        line = f"|{disp}|{acr}|{typ}|{mult}\n"

    # 복합 속성이라면 하위 subAttributeBinding을 재귀적으로 표에 추가
    if comp is not None:
        for sub in comp.findall("S100FC:subAttributeBinding", NS):
            sub_ref = sub.find("S100FC:attribute", NS).attrib["ref"]
            line += write_binding(sub_ref, root, sub, level+1, with_value_col)
    return line

# --- FeatureType → features/*.adoc ---
# 객체 전체 asciidoc 파일 생성 ( 뼈대 )
#
#def process_feature(feature, root):
    code = feature.findtext("S100FC:code", namespaces=NS)
    name = feature.findtext("S100FC:name", default="", namespaces=NS)
    definition = feature.findtext("S100FC:definition", default="", namespaces=NS)
    primitives = [p.text.strip() for p in feature.findall("S100FC:permittedPrimitives", NS)]

    txt = ""
    if definition:
        txt += "===== Definition\n\n" + definition + "\n\n"
    txt += f".{name}의 속성\n"
    txt += '[cols="3,2,1,1", options="header"]\n|===\n'
    # 👇 여기에 primitives 정보 추가
    if primitives:
        txt += f'4+h| Primitives: {", ".join(primitives)}\n'
    txt += "h|Attribute h|Acronym h|Type h|Mult.\n\n"

    for bind in feature.findall("S100FC:attributeBinding", NS):
        attr = bind.find("S100FC:attribute", NS)
        if attr is None: continue
        ref = attr.attrib["ref"]
        txt += write_binding(ref, root, bind, level=0, with_value_col=False)
    txt += "|===\n\n"
    txt += f"include::../features_rules/{code}_rules.adoc[tag={code}]\n"
    return txt
#

### 태원프로님

def process_feature(feature, root):
    code = feature.findtext("S100FC:code", namespaces=NS)
    name = feature.findtext("S100FC:name", default="", namespaces=NS)
    definition = feature.findtext("S100FC:definition", default="", namespaces=NS)
    primitives = [p.text.strip() for p in feature.findall("S100FC:permittedPrimitives", NS)]

    txt = f".{name}의 정의\n"
    txt += '[cols="3,2,1,1", options="header"]\n|===\n'

    # 👇 표 상단에 definition 추가
    if definition:
        txt += f'4+h|*Definition:* {definition}\n'

    # 👇 primitives 정보 추가
    if primitives:
        txt += f'4+h|*Primitives:* {", ".join(primitives)}\n'

    txt += "h|Attribute h|Acronym h|Type h|Mult.\n\n"

    for bind in feature.findall("S100FC:attributeBinding", NS):
        attr = bind.find("S100FC:attribute", NS)
        if attr is None: continue
        ref = attr.attrib["ref"]
        txt += write_binding(ref, root, bind, level=0, with_value_col=False)
    txt += "|===\n\n"
    txt += f"include::../features_rules/{code}_rules.adoc[tag={code}]\n"
    return txt



# FeatureType 객체별로 "코드명.adoc" 파일을 자동 생성하는 함수
def export_features(xml_file, out_dir):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    feats = root.findall(".//S100FC:S100_FC_FeatureType", NS)
    os.makedirs(out_dir, exist_ok=True)
    for f in tqdm(feats, desc="Export features"):
        code = f.findtext("S100FC:code", namespaces=NS)
        if not code: continue
        txt = process_feature(f, root)
        with open(os.path.join(out_dir, f"{code}.adoc"), "w", encoding="utf-8") as fd:
            fd.write(txt)

# --- FeatureType → feature_rules/*_rules.adoc ---
# 객체 전체  asciidoc 파일 생성 ( rules )
def process_rules(feature, root):
    code = feature.findtext("S100FC:code", namespaces=NS)
    txt = f"// tag::{code}[]\n===== Remark\n\n===== Example\n"
    txt += "[cols=\"20,10,5,5,20\", options=\"header\"]\n|===\n|Attribute |Acronym |Type |Mult. |Value\n\n"
    for bind in feature.findall("S100FC:attributeBinding", NS):
        attr = bind.find("S100FC:attribute", NS)
        if attr is None: continue
        ref = attr.attrib["ref"]
        txt += write_binding(ref, root, bind, level=0, with_value_col=True)
    txt += "|===\n\n// end::" + code + "[]\n"
    return txt


# FeatureType 객체별로 "코드명.adoc" 파일을 자동 생성하는 함수
def export_rules(xml_file, out_dir):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    feats = root.findall(".//S100FC:S100_FC_FeatureType", NS)
    os.makedirs(out_dir, exist_ok=True)
    for f in tqdm(feats, desc="Export rules"):
        code = f.findtext("S100FC:code", namespaces=NS)
        if not code: continue
        txt = process_rules(f, root)
        with open(os.path.join(out_dir, f"{code}_rules.adoc"), "w", encoding="utf-8") as fd:
            fd.write(txt)

# --- InformationType → informationTypes/*.adoc ---
# informationtype 객체 전체 asciidoc 파일 생성 (뼈대)
def process_information_type(info, root):
    code = info.findtext("S100FC:code", namespaces=NS)
    name = info.findtext("S100FC:name", default="", namespaces=NS)
    definition = info.findtext("S100FC:definition", default="", namespaces=NS)
    primitives = [p.text.strip() for p in info.findall("S100FC:permittedPrimitives", NS)]

    txt = f".{name}의 정의\n"
    txt += '[cols="3,2,1,1", options="header"]\n|===\n'

    # 👇 definition 정보 상단에 추가
    if definition:
        txt += f'4+h|*Definition:* {definition}\n'

    # 👇 primitives 정보 상단에 추가 (없을 경우 None으로 표기)
    primitive_str = ", ".join(primitives) if primitives else "None"
    txt += f'4+h|*Primitives:* {primitive_str}\n'

    txt += "h|Attribute h|Acronym h|Type h|Mult.\n\n"

    for bind in info.findall("S100FC:attributeBinding", NS):
        attr = bind.find("S100FC:attribute", NS)
        if attr is None:
            continue
        ref = attr.attrib["ref"]
        txt += write_binding(ref, root, bind, level=0, with_value_col=False)

    txt += "|===\n"
    return txt



# imformationtype 객체별로 "코드명.adoc" 파일을 자동 생성하는 함수
def export_information(xml_file, out_dir):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    infos = root.findall(".//S100FC:S100_FC_InformationType", NS)
    os.makedirs(out_dir, exist_ok=True)
    for info in tqdm(infos, desc="Export informationTypes"):
        code = info.findtext("S100FC:code", namespaces=NS)
        if not code: continue
        txt = process_information_type(info, root)
        with open(os.path.join(out_dir, f"{code}.adoc"), "w", encoding="utf-8") as fd:
            fd.write(txt)

# --- 메인 실행부 ---
if __name__ == "__main__":
    XML      = "101_Feature_Catalogue_2.0.0.XML"
    BASE_DIR = os.path.dirname(os.path.abspath(XML))

    export_features(XML, os.path.join(BASE_DIR, "features"))
    export_rules   (XML, os.path.join(BASE_DIR, "feature_rules"))
    export_information(XML, os.path.join(BASE_DIR, "informationTypes"))

    print("✅ features, feature_rules, informationTypes 폴더에 .adoc 파일 생성 완료!")
