# 2026 교육감기 학년별 육상대회 고성 경기일정

고성 출전 학생의 경기일정을 학교·이름으로 찾고, 걸러진 일정을 PNG 이미지로 저장하는 안내 페이지입니다.

- 바로 보기: https://ngryun.github.io/goseong-athletics-2026/
- 학교별 바로가기: 주소 끝에 `#gansung`(간성초) `#dohak`(도학초) `#gonghyeonjin`(공현진초) `#oho`(오호초) `#cheonjin`(천진초) `#goseong`(고성중)

## 일정 갱신

엑셀(`학생별 경기일정.xlsx`)이 바뀌면 아래 명령으로 `index.html`의 데이터를 다시 채운 뒤 커밋·푸시합니다.

```bash
python update_data.py "엑셀 파일 경로"
```

경로를 생략하면 `update_data.py`의 `DEFAULT_XLSX`를 읽습니다. 첫 번째 시트에서 `학교` 머리글 아래 행을
학교·학년·성별·성명·종목·일자·시간·라운드·비고 순서로 읽습니다. (`openpyxl` 필요)
