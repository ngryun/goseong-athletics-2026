# 2026 교육감기 학년별 육상대회 고성 경기일정

고성 출전 학생의 경기일정을 학교·이름으로 찾고, 걸러진 일정을 PNG 이미지로 저장하는 안내 페이지입니다.
경기 결과(순위·기록·결승 진출)는 관리자가 휴대폰으로 입력하면 실시간으로 함께 표시됩니다.

- 바로 보기: https://ngryun.github.io/goseong-athletics-2026/
- 학교별 바로가기: 주소 끝에 `#gansung`(간성초) `#dohak`(도학초) `#gonghyeonjin`(공현진초) `#oho`(오호초) `#cheonjin`(천진초) `#goseong`(고성중)

## 일정 갱신

엑셀(`학생별 경기일정.xlsx`)이 바뀌면 아래 명령으로 `index.html`의 데이터를 다시 채운 뒤 커밋·푸시합니다.

```bash
python update_data.py "엑셀 파일 경로"
```

경로를 생략하면 `update_data.py`의 `DEFAULT_XLSX`를 읽습니다. 첫 번째 시트에서 `학교` 머리글 아래 행을
학교·학년·성별·성명·종목·일자·시간·라운드·비고 순서로 읽습니다. (`openpyxl` 필요)

## 경기 결과 입력

- 관리자 주소: https://ngryun.github.io/goseong-athletics-2026/?admin
  구글 계정으로 로그인한 뒤 학생 이름이나 일정 줄을 누르면 순위·기록·결승 진출·기권 등을 입력할 수 있습니다.
  카카오톡 안 브라우저에서는 구글 로그인이 막히므로 Safari나 Chrome으로 엽니다.
- 결과는 Firebase 프로젝트 `goseong-athletics-2026`의 Firestore 문서 `meet/results` 하나에 모이고, 페이지가 실시간으로 받아 보여 줍니다.
  계주는 팀 단위로, `결승(진출 시)`는 `결승`으로 묶어 저장하므로 엑셀의 라운드 표기가 바뀌어도 결과가 이어집니다.
- 입력 권한은 `firestore.rules`에 적힌 처음 관리자와, 관리자 화면의 "관리자"에서 추가한 계정에만 있습니다.
  규칙을 고치면 `firebase deploy --only firestore`로 반영합니다.
