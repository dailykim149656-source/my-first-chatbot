import streamlit as st
import os
import time
import io
from openai import AzureOpenAI
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()

# 환경 변수 확인 및 검증
required_env_vars = {
    "AZURE_OAI_ENDPOINT": os.getenv("AZURE_OAI_ENDPOINT"),
    "AZURE_OAI_KEY": os.getenv("AZURE_OAI_KEY"),
    "SEARCH_ENDPOINT": os.getenv("SEARCH_ENDPOINT"),
    "SEARCH_KEY": os.getenv("SEARCH_KEY"),
}

missing_vars = [key for key, value in required_env_vars.items() if not value]

if missing_vars:
    st.error(f"❌ 다음 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
    st.info("""
    💡 해결 방법:
    1. 프로젝트 폴더에 .env 파일이 있는지 확인
    2. .env 파일에 다음 값들이 올바르게 설정되어 있는지 확인:
       - AZURE_OAI_ENDPOINT=https://your-resource.openai.azure.com/
       - AZURE_OAI_KEY=your-api-key
       - AZURE_OAI_DEPLOYMENT=your-deployment-name
       - SEARCH_ENDPOINT=https://your-search.search.windows.net
       - SEARCH_KEY=your-search-key
    3. 값에 공백이나 따옴표가 없는지 확인
    4. 자세한 내용은 TROUBLESHOOTING.md 파일을 참고하세요
    """)
    st.code("""
# .env 파일 예시
AZURE_OAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OAI_KEY=abc123def456...
AZURE_OAI_DEPLOYMENT=gpt-4o-mini
SEARCH_ENDPOINT=https://your-search.search.windows.net
SEARCH_KEY=search-key-here
    """, language="bash")
    st.stop()

# Endpoint 형식 검증
endpoint = os.getenv("AZURE_OAI_ENDPOINT")
if endpoint and not endpoint.startswith("https://"):
    st.error("❌ AZURE_OAI_ENDPOINT는 https://로 시작해야 합니다.")
    st.info(f"현재 값: {endpoint}")
    st.stop()

if endpoint and ".openai.azure.com" not in endpoint:
    st.warning("⚠️ AZURE_OAI_ENDPOINT 형식을 확인하세요. (예: https://your-resource.openai.azure.com/)")

st.set_page_config(
    page_title="반도체 공정 전문가 챗봇",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 반도체 공정 학습 도우미 SEMI(쎄미)")
st.caption("💡 학부생을 위한 AI 기반 반도체 공정 이론 & 시각화 챗봇")

# 2. Azure OpenAI 클라이언트 설정
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OAI_KEY"),
    api_version="2024-05-01-preview"
)

# 3. Azure AI Search 설정
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("SEARCH_KEY")
SEARCH_INDEX = "semicon-proc-rag"
DEPLOYMENT_NAME = os.getenv("AZURE_OAI_DEPLOYMENT", "gpt-4o-mini")
EMBEDDING_DEPLOYMENT = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")

# 4. 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# 5. 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    use_rag = st.checkbox("RAG 검색 활성화", value=True, help="반도체 공정 전문 지식 활용")
    use_code_interpreter = st.checkbox("코드 인터프리터 활성화", value=True, help="데이터 시각화 및 계산")
    
    st.divider()
    st.subheader("💡 사용 가이드")
    
    # 탭으로 구분
    tab1, tab2 = st.tabs(["🔍 이론 질문", "📊 시각화"])
    
    with tab1:
        st.markdown("""
        **반도체 공정 이론 질문 예시:**
        
        🎯 **공정 원리**
        - "포토리소그래피 공정의 원리를 설명해줘"
        - "습식 에칭과 건식 에칭의 차이는?"
        - "CVD와 PVD의 장단점을 비교해줘"
        
        📐 **공정 파라미터**
        - "CMP 공정의 주요 파라미터는 뭐야?"
        - "이온주입에서 도즈와 에너지의 역할은?"
        - "플라즈마 에칭의 선택비란?"
        
        🔬 **심화 질문**
        - "EUV 리소그래피가 ArF보다 좋은 이유는?"
        - "damascene 공정을 설명해줘"
        - "열산화와 CVD 산화막의 차이는?"
        """)
    
    with tab2:
        st.markdown("""
        **시각화 요청 예시 (수치 포함):**
        
        📊 **막대 그래프**
        ```
        반도체 주요 공정의 처리 시간을 
        막대 그래프로 그려줘.
        
        - Photolithography: 45분
        - CVD: 30분
        - Etching: 25분
        - CMP: 20분
        ```
        
        📈 **꺾은선 그래프**
        ```
        온도에 따른 CVD 증착률 변화를
        꺾은선 그래프로 그려줘.
        
        300°C: 10 nm/min
        500°C: 30 nm/min
        700°C: 60 nm/min
        ```
        
        🥧 **파이 차트**
        ```
        반도체 제조 공정별 비용 분포를
        파이 차트로 그려줘.
        
        - Lithography: 35%
        - Etching: 25%
        - Deposition: 20%
        - Others: 20%
        ```
        
        💡 **Tip:** 그래프 레이블은 영문으로 
        표시되며, 설명은 한글로 제공됩니다.
        """)
    
    st.divider()
    
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.assistant_id = None
        st.session_state.thread_id = None
        st.rerun()
    
    st.caption("🎓 학부생을 위한 반도체 공정 학습 도우미")

# 6. 기존 대화 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # 이미지가 있으면 표시
        if "images" in message:
            for img in message["images"]:
                st.image(io.BytesIO(img), use_column_width=True)

# 7. 사용자 입력
if prompt := st.chat_input("반도체 공정에 대해 궁금한 것을 물어보세요! (예: 포토리소그래피란 뭐야?)"):
    # (1) 사용자 메시지 화면에 표시 & 저장
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # (2) RAG 기반 Chat Completions 응답
    with st.chat_message("assistant"):
        try:
            # RAG용 메시지 구성
            if use_rag:
                # Azure AI Search를 data source로 사용
                response = client.chat.completions.create(
                    model=DEPLOYMENT_NAME,
                    messages=[
                        {"role": "system", "content": "당신은 학부생을 위한 반도체 공정 학습 도우미입니다. 학부 수업 수준의 반도체 공정 이론을 쉽고 명확하게 설명하세요. 전문 용어를 사용할 때는 처음에 간단한 설명을 덧붙이고, 복잡한 개념은 단계적으로 설명하세요. 학생들이 이해하기 쉽도록 예시와 비유를 활용하세요."},
                        *[{"role": m["role"], "content": m["content"]} 
                          for m in st.session_state.messages]
                    ],
                    extra_body={
                        "data_sources": [
                            {
                                "type": "azure_search",
                                "parameters": {
                                    "endpoint": SEARCH_ENDPOINT,
                                    "index_name": SEARCH_INDEX,
                                    "query_type": "vector",
                                    "in_scope": True,
                                    "role_information": "당신은 학부생을 위한 반도체 공정 학습 도우미입니다. 학부 수준의 이론을 쉽게 설명하세요.",
                                    "strictness": 3,
                                    "top_n_documents": 5,
                                    "authentication": {
                                        "type": "api_key",
                                        "key": SEARCH_KEY
                                    },
                                    "embedding_dependency": {
                                        "type": "deployment_name",
                                        "deployment_name": EMBEDDING_DEPLOYMENT
                                    }
                                }
                            }
                        ]
                    }
                )
            else:
                # 일반 응답
                response = client.chat.completions.create(
                    model=DEPLOYMENT_NAME,
                    messages=[
                        {"role": "system", "content": "당신은 학부생을 위한 반도체 공정 학습 도우미입니다. 쉽고 친절하게 설명하세요."},
                        *[{"role": m["role"], "content": m["content"]} 
                          for m in st.session_state.messages]
                    ]
                )
            
            assistant_reply = response.choices[0].message.content
            
            # 컨텍스트 정보 표시 (RAG 사용 시)
            if use_rag and hasattr(response.choices[0].message, 'context'):
                context = response.choices[0].message.context
                if context and 'citations' in context:
                    with st.expander("📄 참조 문서"):
                        for citation in context['citations']:
                            st.markdown(f"- {citation.get('title', 'Document')}")
            
            st.markdown(assistant_reply)
            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

        except Exception as e:
            st.error(f"❌ 오류 발생: {str(e)}")
            st.info("💡 .env 파일의 SEARCH_ENDPOINT와 SEARCH_KEY가 올바르게 설정되어 있는지 확인하세요.")

    # (3) 코드 인터프리터 실행 여부 판단
    visualization_keywords = ["그래프", "plot", "차트", "그려줘", "시각화", "플롯", "보여줘", "비교", "분포"]
    calculation_keywords = ["계산", "코드", "분석", "통계", "평균", "합계"]
    
    needs_code_interpreter = use_code_interpreter and any(
        keyword in prompt.lower() for keyword in visualization_keywords + calculation_keywords
    )
    
    if needs_code_interpreter:
        with st.spinner("🖥️ 코드 인터프리터로 분석 중..."):
            try:
                # Assistants API 준비
                if st.session_state.assistant_id is None:
                    assistant = client.beta.assistants.create(
                        model=DEPLOYMENT_NAME,
                        instructions="""You are a helpful assistant for undergraduate students learning semiconductor processes.

**CRITICAL FONT RULE:**
The code interpreter does NOT have Korean fonts. Use ONLY English for all graph text (titles, labels, legends).

**Your role:**
- Help students visualize and understand semiconductor process data
- Create clear, educational graphs
- Explain results in simple terms (in Korean in text, not graphs)

**For ALL visualizations:**

1. **Use English ONLY in graphs:**
   - Titles, axis labels, legends, annotations
   - Keep labels simple and clear for students

2. **Font settings (mandatory first):**
```python
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['axes.unicode_minus'] = False
```

3. **Common terms for students:**
   - 포토리소그래피 → "Photolithography"
   - 에칭 → "Etching"  
   - 증착 → "Deposition"
   - 이온주입 → "Ion Implantation"
   - 공정 시간 → "Process Time"
   - 온도 → "Temperature"
   - 압력 → "Pressure"

4. **Graph style (educational & clear):**
```python
plt.figure(figsize=(10, 6))
plt.title('Clear Descriptive Title', fontsize=14, fontweight='bold')
plt.xlabel('X-axis Label (unit)', fontsize=12)
plt.ylabel('Y-axis Label (unit)', fontsize=12)
plt.grid(True, alpha=0.3, linestyle='--')
plt.legend(loc='best', fontsize=10)
plt.tight_layout()

# Add value labels on bars for clarity
for i, v in enumerate(values):
    plt.text(i, v, str(v), ha='center', va='bottom')
```

5. **Make it educational:**
   - Use clear, readable fonts (size 10-14)
   - Add gridlines for easy reading
   - Label data points when helpful
   - Use distinct colors
   - Include units in labels

**Remember:**
- Graphs: English only (clean display)
- Code comments: Can be Korean
- Explanations to student: Korean (easy to understand)

Example good title: "CVD Deposition Rate vs Temperature"
Example good label: "Processing Time (minutes)"
""",
                        tools=[{"type": "code_interpreter"}],
                        tool_resources={"code_interpreter": {"file_ids": []}},
                        temperature=0.3
                    )
                    st.session_state.assistant_id = assistant.id

                if st.session_state.thread_id is None:
                    thread = client.beta.threads.create()
                    st.session_state.thread_id = thread.id

                # 사용자 요청 추가 (RAG 응답 포함)
                enhanced_prompt = f"""
                이전 답변: {assistant_reply}
                
                사용자 요청: {prompt}
                
                위 내용을 바탕으로 데이터 시각화 또는 계산을 수행하세요.
                """
                
                client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=enhanced_prompt
                )

                # 실행
                run = client.beta.threads.runs.create(
                    thread_id=st.session_state.thread_id,
                    assistant_id=st.session_state.assistant_id
                )

                # 상태 폴링
                max_wait = 60  # 최대 60초 대기
                start_time = time.time()
                while True:
                    run = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id
                    )
                    if run.status in ["queued", "in_progress"]:
                        if time.time() - start_time > max_wait:
                            st.warning("⏱️ 처리 시간이 초과되었습니다.")
                            break
                        time.sleep(1)
                        continue
                    else:
                        break

                if run.status == "completed":
                    msgs = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
                    images = []
                    code_output = None
                    
                    for m in reversed(msgs.data):
                        if m.role == "assistant":
                            for c in m.content:
                                if c.type == "image_file":
                                    fid = c.image_file.file_id
                                    resp = client.files.content(fid)
                                    img_bytes = resp.read()
                                    images.append(img_bytes)
                                elif c.type == "text":
                                    code_output = c.text.value
                            break

                    if images or code_output:
                        with st.chat_message("assistant"):
                            st.markdown("### 📊 분석 결과")
                            
                            if code_output:
                                st.markdown(code_output)
                            
                            if images:
                                st.markdown("#### 생성된 시각화")
                                for idx, img in enumerate(images):
                                    st.image(io.BytesIO(img), caption=f"분석 결과 {idx+1}", use_column_width=True)
                                
                                # 이미지를 메시지에 저장
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": "📊 시각화 결과",
                                    "images": images
                                })
                    else:
                        st.info("ℹ️ 시각화 결과가 생성되지 않았습니다.")
                        
                elif run.status == "failed":
                    st.error(f"❌ 실행 실패: {run.last_error.message if run.last_error else '알 수 없는 오류'}")
                else:
                    st.warning(f"⚠️ 예상치 못한 상태: {run.status}")
                    
            except Exception as e:
                st.error(f"❌ 코드 인터프리터 오류: {str(e)}")

# 8. 푸터
st.divider()
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.caption("🎓 반도체 공정 학습 도우미 | 학부생을 위한 AI 기반 학습 도구")
    st.caption("💡 RAG 검색 + 코드 인터프리터 시각화 | Powered by Azure OpenAI")

