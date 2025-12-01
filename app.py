
import streamlit as st
import os
import time
import io
from openai import AzureOpenAI
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()

st.title("🤖 나의 첫 AI 챗봇 + 코드 인터프리터")

# 2. Azure OpenAI 클라이언트 설정
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OAI_KEY"),
    api_version="2024-05-01-preview"  # Assistants API 버전
)

# 3. 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# 4. 기존 대화 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 사용자 입력
if prompt := st.chat_input("무엇을 도와드릴까요?"):
    # (1) 사용자 메시지 화면에 표시 & 저장
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # (2) 일반 Chat Completions 응답
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Azure 배포 이름
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
        )
        assistant_reply = response.choices[0].message.content
        st.markdown(assistant_reply)

    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

    # (3) 코드 인터프리터 실행 여부 판단 (간단한 조건)
    if any(keyword in prompt.lower() for keyword in ["그래프", "plot", "그려줘", "계산", "코드"]):
        st.markdown("### 🖥️ 코드 인터프리터 실행 중...")
        # Assistants API 준비
        if st.session_state.assistant_id is None:
            assistant = client.beta.assistants.create(
                model="gpt-4o-mini",
                instructions="너는 코드 인터프리터를 사용할 수 있는 분석 도우미야.",
                tools=[{"type": "code_interpreter"}],
                tool_resources={"code_interpreter": {"file_ids": []}},
                temperature=0.7,
                top_p=1
            )
            st.session_state.assistant_id = assistant.id

        if st.session_state.thread_id is None:
            thread = client.beta.threads.create()
            st.session_state.thread_id = thread.id

        # 사용자 요청 추가
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )

        # 실행
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=st.session_state.assistant_id
        )

        # 상태 폴링
        while True:
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
            if run.status in ["queued", "in_progress"]:
                time.sleep(1)
                continue
            else:
                break

        if run.status == "completed":
            msgs = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
            images = []
            for m in reversed(msgs.data):
                if m.role == "assistant":
                    for c in m.content:
                        if c.type == "image_file":
                            fid = c.image_file.file_id
                            resp = client.files.content(fid)
                            img_bytes = resp.read()
                            images.append(img_bytes)
                    break

            if images:
                st.markdown("#### ✅ 생성된 이미지")
                for img in images:
                    st.image(io.BytesIO(img), caption="Code Interpreter Output", use_column_width=True)
            else:
                st.markdown("_이미지 결과가 없습니다._")
        else:
            st.error(f"Run status: {run.status}")
