# Instagram 프로필 & 미디어 다운로더 (한국어)

## ⚠️ 주의사항

**해당 사용자의 명시적인 동의 없이 Instagram에서 팔로워 목록이나 하이라이트 등 공개되지 않은 정보를 추출하거나 재배포하는 행위는 Instagram의 서비스 약관에 따라 엄격히 금지됩니다.**
**이를 위반할 경우 계정 정지 등의 불이익을 받을 수 있으며, 법적인 문제가 발생할 수도 있습니다. 본 프로그램은 연구 및 개인 학습 목적으로만 사용해야 하며, 어떠한 불법적이거나 윤리적으로 문제가 되는 목적으로도 사용되어서는 안 됩니다. 모든 책임은 사용자에게 있습니다.**

---

## 프로젝트 설명

이 프로그램은 Instagram 사용자의 **프로필 정보, 팔로워 목록 및 하이라이트 미디어(사진/동영상)**를 조회하고 다운로드할 수 있는 GUI 기반 도구입니다.

---

## 주요 기능

* **프로필 정보 조회:** 대상 사용자의 공개 프로필 정보 및 총 팔로워 수를 확인합니다.
* **하이라이트 목록 조회 및 미디어 다운로드:** 대상 사용자의 하이라이트 목록을 불러오고, 각 하이라이트 별로 포함된 미디어(사진 및 동영상)를 선택적으로 다운로드하여 저장할 수 있습니다.
* **팔로워 목록 추출:** 대상 사용자의 모든 팔로워 계정(사용자 ID, 닉네임, 전체 이름)을 추출하여 텍스트 파일로 저장할 수 있습니다.

---

## 사용을 위한 필수 정보

본 프로그램을 사용하기 위해서는 다음과 같은 Instagram 인증 정보가 필요합니다. 이 정보는 로그인한 상태에서 브라우저의 개발자 도구를 통해 얻을 수 있습니다.

* **대상 사용자 이름 (Username):** 정보를 조회하고자 하는 Instagram 사용자의 닉네임입니다.
* **Session ID (sessionid):** Instagram 로그인 세션을 유지하는 데 사용되는 쿠키 값입니다.
* **CSRF Token (csrftoken):** 사이트 간 요청 위조 방지 토큰으로, API 요청 시 필요합니다.

# Instagram Profile & Media Downloader (English Instruction)

## ⚠️ Caution

**Extracting or redistributing non-public information such as follower lists or highlight media from Instagram without the explicit consent of the respective user is strictly prohibited by Instagram's Terms of Service.**
**Violation may result in penalties such as account suspension and could lead to legal issues. This program should only be used for research and personal learning purposes and must not be used for any illegal or ethically questionable objectives. All responsibility lies with the user.**

---

## Project Description

This program is a GUI-based tool designed to retrieve and download **profile information, follower lists, and highlight media (photos/videos)** of an Instagram user.

**Please note that this program is written in Korean.**

---

## Key Features

* **Profile Information Retrieval:** View the target user's public profile information and total follower count.
* **Highlight List Retrieval & Media Download:** Fetch the target user's highlight reels and selectively download the contained media (photos and videos) for storage.
* **Follower List Extraction:** Extract all follower accounts (User ID, Username, Full Name) of the target user and save them into a text file.

---

## Required Information for Use

To use this program, the following Instagram authentication details are necessary. This information can typically be obtained from your browser's developer tools while logged into Instagram.

* **Target Username:** The Instagram username of the profile you wish to retrieve information from.
* **Session ID (sessionid):** A cookie value used to maintain your Instagram login session.
* **CSRF Token (csrftoken):** An anti-cross-site request forgery token required for API requests.
