import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# --- 1. CẤU HÌNH TRANG & STYLE ---
st.set_page_config(
    page_title="Global Climate Strategic Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded" # Mở rộng sidebar mặc định
)

# --- CSS CUSTOM ĐỂ DASHBOARD ĐẸP HƠN ---
st.markdown("""
<style>
    /* Style cho Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: scale(1.02);
        border-color: #ff4b4b;
    }
    /* Chỉnh font tiêu đề */
    h1 {
        color: #0e1117;
        font-family: 'Helvetica Neue', sans-serif;
    }
    h2, h3 {
        color: #262730;
    }
    /* Style cho các hộp thông báo (Info/Success) */
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
# Danh sách các trang và Icon tương ứng
PAGES = {
    "Overview": "🌍 Tổng Quan",
    "BQ1": "⚡ BQ1: Response Time",
    "BQ2": "🇨🇳 BQ2: Scale Paradox",
    "Conclusion": "🏁 Kết Luận & Action"
}

if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'Overview'

def navigate_to(page):
    st.session_state['current_page'] = page
    st.rerun()

# --- SIDEBAR MENU ---
with st.sidebar:
    st.title("🧭 Navigation")
    st.markdown("---")
    
    # Tạo Radio button làm menu, đồng bộ với session_state
    selected_page = st.radio(
        "Di chuyển nhanh đến:",
        options=list(PAGES.keys()),
        format_func=lambda x: PAGES[x],
        index=list(PAGES.keys()).index(st.session_state['current_page']),
        key="nav_radio"
    )
    
    # Cập nhật lại session state nếu người dùng chọn từ sidebar
    if selected_page != st.session_state['current_page']:
        st.session_state['current_page'] = selected_page
        st.rerun()
    
    st.markdown("---")
    st.info("**Project:** Global Climate Impact\n\n**Data:** 2020-2025\n\n**Status:** Strategic Analysis")

# --- 2. XỬ LÝ DỮ LIỆU (GIỮ NGUYÊN LOGIC CỦA BẠN) ---
@st.cache_data
def load_and_process_data():
    try:
        df = pd.read_csv('global_climate_events_economic_impact_2020_2025.csv')
    except FileNotFoundError:
        st.error("⚠️ Không tìm thấy file dữ liệu. Vui lòng kiểm tra lại.")
        return None

    # Basic Cleaning
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['year'].astype(int)
    
    # Features
    developed_countries = [
        'United States', 'Japan', 'Germany', 'United Kingdom', 'France', 'Italy', 'Canada',
        'Australia', 'South Korea', 'Netherlands', 'Switzerland', 'Sweden', 'Belgium',
        'Austria', 'Denmark', 'Finland', 'Norway', 'Ireland', 'New Zealand', 'Singapore'
    ]
    df['is_developed'] = df['country'].isin(developed_countries)
    df['dev_status'] = df['is_developed'].map({True: 'Developed', False: 'Developing'})

    bins_resp = [0, 12, 24, np.inf]
    labels_resp = ['<12h (Nhanh)', '12-24h (Trung bình)', '>24h (Chậm)']
    df['response_bin'] = pd.cut(df['response_time_hours'], bins=bins_resp, labels=labels_resp, include_lowest=True)

    df['death_rate'] = (df['deaths'] / df['affected_population']) * 100
    df['injury_rate'] = (df['injuries'] / df['affected_population']) * 100

    def get_continent(country):
        asia = ['China', 'India', 'Japan', 'South Korea', 'Indonesia', 'Philippines', 'Vietnam', 'Thailand', 'Singapore']
        europe = ['Germany', 'United Kingdom', 'France', 'Italy', 'Netherlands', 'Switzerland', 'Sweden', 'Belgium', 'Austria', 'Poland']
        americas = ['United States', 'Canada', 'Brazil', 'Mexico', 'Argentina']
        africa = ['Nigeria', 'Egypt', 'South Africa', 'Kenya', 'Ethiopia']
        if country in asia: return 'Asia'
        if country in europe: return 'Europe'
        if country in americas: return 'Americas'
        if country in africa: return 'Africa'
        return 'Other'
    
    df['continent'] = df['country'].apply(get_continent)
    bins_pop = [0, 100000, 1000000, 5000000, df['affected_population'].max()+1]
    labels_pop = ['<100k', '100k–1M', '1M–5M', '>5M (Mega-event)']
    df['scale'] = pd.cut(df['affected_population'], bins=bins_pop, labels=labels_pop)
    df['log_impact'] = np.log1p(df['economic_impact_million_usd'])

    return df

df = load_and_process_data()

# --- 3. HÀM RENDER CÁC TRANG ---

def render_overview():
    st.markdown("# 🌍 Global Climate Impact Dashboard")
    st.markdown("### *Chiến lược Ứng phó Thiên tai dựa trên Dữ liệu Thực tế (2020-2025)*")
    st.markdown("---")
    
    # --- KPI CARDS (ĐÃ CÓ CSS ĐẸP) ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🌪️ Tổng Sự Kiện", f"{len(df):,}")
    k2.metric("💸 Tổng Thiệt Hại", f"${df['economic_impact_million_usd'].sum():,.0f} M")
    k3.metric("👥 Người bị ảnh hưởng", f"{df['affected_population'].sum():,.0f}")
    k4.metric("🚑 Tốc độ Ứng phó TB", f"{df['response_time_hours'].mean():.1f} giờ")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- HÀNG 2: MAP & BAR ---
    st.subheader("1. Phân Bố Địa Lý & Tần Suất")
    col1, col2 = st.columns([3, 2])
    
    with col1:
        country_map_data = df.groupby('country').agg({
            'economic_impact_million_usd': 'sum',
            'event_id': 'count'
        }).reset_index()
        
        fig_map = px.choropleth(
            country_map_data,
            locations="country",
            locationmode="country names",
            color="economic_impact_million_usd",
            hover_name="country",
            hover_data=["event_id"],
            color_continuous_scale="Reds",
            title="<b>Bản đồ Nhiệt: Tổng thiệt hại Kinh tế</b>",
            projection="natural earth"
        )
        fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)
        
    with col2:
        event_counts = df['event_type'].value_counts().reset_index()
        event_counts.columns = ['Loại', 'Số lượng']
        fig_bar = px.bar(event_counts, x='Số lượng', y='Loại', orientation='h', 
                         title="<b>Tần suất Loại thiên tai</b>", color='Số lượng', color_continuous_scale='Blues')
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- HÀNG 3: TOP 15 & HEATMAP ---
    st.subheader("2. Top Quốc Gia & Tương Quan Biến Số")
    c3, c4 = st.columns(2)
    
    with c3:
        top15 = df['country'].value_counts().head(15).reset_index()
        top15.columns = ['Quốc gia', 'Số sự kiện']
        fig_top15 = px.bar(
            top15, x='Số sự kiện', y='Quốc gia', orientation='h', 
            color='Số sự kiện', color_continuous_scale='plasma',
            title="<b>Top 15 Quốc gia có tần suất cao nhất</b>"
        )
        fig_top15.update_layout(yaxis={'categoryorder':'total ascending'}, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_top15, use_container_width=True)

    with c4:
        st.markdown("**Heatmap Tương Quan (Pearson)**")
        key_cols = ['economic_impact_million_usd', 'deaths', 'injuries', 
                    'affected_population', 'response_time_hours', 'international_aid_million_usd']
        corr_matrix = df[key_cols].corr()
        fig_corr, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=.5, ax=ax)
        ax.set_title("Correlation Matrix", fontsize=14)
        st.pyplot(fig_corr)

    st.markdown("---")

    # --- INSIGHT BOX ---
    st.subheader("3. 🔍 Key Takeaways từ EDA")
    st.info("""
    **💡 Các phát hiện nền tảng:**
    1.  **Dữ liệu lệch (Skewness):** Hầu hết các biến số đều lệch phải -> Cần phân tích theo nhóm (Binning) thay vì trung bình.
    2.  **Nghịch lý Tương quan:** Tương quan tuyến tính giữa `response_time` và `deaths` gần bằng 0. Điều này gợi ý mối quan hệ có "ngưỡng" (Threshold).
    3.  **Điểm nóng:** Thiên tai tập trung lớn ở Châu Á (China, India) và Mỹ.
    """)

    # Nút Next
    st.markdown("<br>", unsafe_allow_html=True)
    col_empty, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button("Phân tích BQ1 ➡️", type="primary", use_container_width=True):
            navigate_to('BQ1')

def render_bq1():
    st.markdown("# ⚡ BQ1: Response time có ảnh hưởng đến số lượng người chết và bị thương không? Ảnh hưởng như thế nào? Và sự khác biệt địa lý giữa nước đã & đang phát triển là gì?
")
    st.markdown("""
    
    <br>
    """, unsafe_allow_html=True)
    
    # Tính toán
    avg_death_fast = df[df['response_time_hours'] <= 24]['death_rate'].mean()
    avg_death_slow = df[df['response_time_hours'] > 24]['death_rate'].mean()
    if avg_death_fast == 0: avg_death_fast = 0.000001 
    diff_percent = ((avg_death_slow - avg_death_fast) / avg_death_fast) * 100

    # DQ1.1
    st.subheader("📌 DQ1.1: Tốc độ ứng phó ảnh hưởng thế nào đến tỷ lệ tử vong?'")
    c1, c2 = st.columns([1, 1])
    with c1:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=df, x='response_bin', y='death_rate', palette='Reds', ci=None, ax=ax)
        ax.set_title("Tỷ lệ Tử vong (%) theo Tốc độ Ứng phó", fontweight='bold')
        st.pyplot(fig)
    with c2:
        st.success(f"""
        **✅ Bằng chứng Dữ liệu:**
        * **Phản ứng nhanh (<24h):** Tỷ lệ tử vong thấp và ổn định ({avg_death_fast:.4f}%).
        * **Phản ứng chậm (>24h):** Tỷ lệ tử vong tăng vọt lên {avg_death_slow:.4f}%.
        * **Kết luận:** Chậm hơn 24h làm tăng rủi ro tử vong thêm **{diff_percent:.0f}%**.
        """)

    st.markdown("---")

    # DQ3.2 & DQ3.3
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("📌 DQ1.2: Các nước giàu (Developed) có thực sự làm tốt hơn nước nghèo?")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.boxplot(data=df, x='dev_status', y='response_time_hours', palette='Set2', ax=ax)
        ax.set_title("Tốc độ: Developing NHANH HƠN Developed", fontweight='bold')
        st.pyplot(fig)
        st.error("**Nghịch lý:** Nước phát triển (Developed) phản ứng trung bình chậm hơn nước đang phát triển, và khi chậm thì hậu quả nghiêm trọng hơn.")

    with c4:
        st.subheader("📌 DQ1.3: Phản ứng nhanh có cứu được cơ sở hạ tầng (nhà cửa, cầu đường) không?")
        infra_trend = df.groupby('response_bin')['infrastructure_damage_score'].mean().reset_index()
        fig = px.line(infra_trend, x='response_bin', y='infrastructure_damage_score', markers=True,
                      title="<b>Điểm Thiệt hại Hạ tầng (0-10) theo Tốc độ</b>",
                      labels={'infrastructure_damage_score': 'Avg Damage Score'})
        st.plotly_chart(fig, use_container_width=True)
        st.warning("**Insight:** Tốc độ nhanh KHÔNG cứu được hạ tầng (Đường biểu đồ đi ngang). Hạ tầng thường sập ngay lập tức, cứu hộ chỉ cứu được người.")

    # ACTION BOX
    st.markdown("### 🚀 HÀNH ĐỘNG ĐỀ XUẤT")
    st.info("1. **KPI Cứng:** 90% sự kiện phải tiếp cận <24h.\n2. **Chiến lược:** Trong 24h đầu, dồn 100% lực lượng cứu người, bỏ qua tài sản.\n3. **Cảnh báo:** Developed countries cần rà soát lại quy trình hành chính.")

    # Navigation Buttons
    st.markdown("<br>", unsafe_allow_html=True)
    col_p, col_empty, col_n = st.columns([1, 3, 1])
    with col_p:
        if st.button("⬅️ Quay lại", use_container_width=True):
            navigate_to('Overview')
    with col_n:
        if st.button("Phân tích BQ2 ➡️", type="primary", use_container_width=True):
            navigate_to('BQ2')

def render_bq2():
    st.markdown("# BQ2: Tỷ lệ tử vong và response time ảnh hưởng thế nào đến các sự kiện lớn/nhỏ? Liệu có theo triết lý thông thường “càng nhỏ càng dễ phản ứng”? (Scale Paradox)")
    st.markdown("""
    <br>
    """, unsafe_allow_html=True)
    
    st.subheader("📌 DQ2.1 & DQ2.2: Quy mô ảnh hưởng như thế nào đối với tốc độ phản ứng và tỉ lệ chết?")
    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=df, x='scale', y='response_time_hours', palette='Blues_d', ci=None, ax=ax)
        ax.set_title("DQ2.1: Response Time (Mega-event nhanh nhất!)", fontweight='bold')
        st.pyplot(fig)
    with col2:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=df, x='scale', y='death_rate', palette='Reds_d', ci=None, ax=ax)
        ax.set_title("DQ2.2: Death Rate (Mega-event thấp nhất!)", fontweight='bold')
        st.pyplot(fig)
    
    st.markdown("---")
    
    # DQ2.3
    st.markdown("### **DQ2.3: Quốc gia nào chiếm đa số các mega-event (>5M người)?**")
    mega_events = df[df['scale'] == '>5M (Mega-event)']
    top10_mega = mega_events['country'].value_counts().head(10).reset_index()
    top10_mega.columns = ['Quốc gia', 'Số sự kiện Mega']
    
    total_mega = len(mega_events)
    china_india_count = mega_events[mega_events['country'].isin(['China', 'India'])].shape[0]
    percent_ci = (china_india_count / total_mega) * 100
    
    c_d3_1, c_d3_2 = st.columns([2, 1])
    with c_d3_1:
        fig_dq3 = px.bar(top10_mega, x='Số sự kiện Mega', y='Quốc gia', orientation='h', 
                         text='Số sự kiện Mega', title="<b>Top 10 Quốc gia có Mega-event</b>",
                         color='Số sự kiện Mega', color_continuous_scale='Reds')
        fig_dq3.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_dq3, use_container_width=True)
    with c_d3_2:
        st.warning(f"""
        **🕵️‍♂️ Thủ phạm được tìm thấy:**
        China và India áp đảo hoàn toàn.
        * **Chiếm tỷ trọng:** {percent_ci:.1f}% tổng số Mega-events.
        * -> Đây chính là chìa khóa giải mã nghịch lý.
        """)

    st.markdown("---")
    
    # DQ2.4 & DQ2.5
    st.subheader("📌 DQ2.4 & DQ2.5: Kiểm chứng giả thuyết")
    
    exclude_giants = st.checkbox("🛑 **Loại bỏ China & India** ra khỏi dữ liệu để kiểm chứng?", value=False)

    if exclude_giants:
        df_viz = df[~df['country'].isin(['China', 'India'])]
        insight_text = "👉 **Kết quả:** Khi loại bỏ China & India -> **Nghịch lý BIẾN MẤT!** Mega-events trở nên chậm chạp đúng như quy luật thông thường."
        insight_type = st.error
    else:
        df_viz = df
        insight_text = "👉 **Hiện tại:** Dữ liệu bao gồm China & India (Năng lực huy động 'thời chiến' cực mạnh)."
        insight_type = st.warning

    col3, col4 = st.columns(2)
    with col3:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=df_viz, x='scale', y='response_time_hours', palette='viridis', ci=None, ax=ax)
        ax.set_title(f"Response Time ({'NO China/India' if exclude_giants else 'ALL'})", fontweight='bold')
        ax.set_ylabel("Giờ")
        st.pyplot(fig)
    
    with col4:
        insight_type(insight_text)
        if not exclude_giants:
            china_india_df = df[df['country'].isin(['China', 'India'])].assign(group='China & India')
            others_df = df[~df['country'].isin(['China', 'India'])].assign(group='Rest of World')
            comp_df = pd.concat([china_india_df, others_df])
            
            fig, ax = plt.subplots(figsize=(8, 3.5))
            sns.boxplot(data=comp_df, x='response_time_hours', y='group', palette='magma', ax=ax)
            st.pyplot(fig)
            st.caption("China & India nhanh hơn thế giới trung bình 36%.")

    st.info("🚀 **ACTION:** Thế giới cần học mô hình 'Mega-event Response' và chuyển giao công nghệ từ China/India.")

    # Nav
    st.markdown("<br>", unsafe_allow_html=True)
    col_p, col_empty, col_n = st.columns([1, 3, 1])
    with col_p:
        if st.button("⬅️ Quay lại", use_container_width=True):
            navigate_to('BQ1')
    with col_n:
        if st.button("Kết luận & Action 🏁", type="primary", use_container_width=True):
            navigate_to('Conclusion')

def render_conclusion():
    st.markdown("# 🏁 Tổng Kết & Khuyến Nghị Chiến Lược")
    st.markdown("### *Bức tranh toàn cảnh: Từ dữ liệu đến hành động thực tiễn*")

    # Metrics
    st.markdown("#### 🏆 Top Key Insights")
    c1, c2, c3 = st.columns(3)
    c1.metric(label="Quy tắc 24h Vàng", value="-52% Deaths", delta="Nếu phản ứng <24h")
    c2.metric(label="China & India Factor", value="36% Faster", delta="So với thế giới", delta_color="normal")
    c3.metric(label="Developed Risk", value="+3.8x Deaths", delta="Khi phản ứng chậm >24h", delta_color="inverse")

    st.markdown("---")

    # Matrix
    st.subheader("📊 Ma Trận Hiệu Quả Quốc Gia (Performance Matrix)")
    st.markdown("*Trục X: Tốc độ (Càng trái càng tốt) | Trục Y: Tỷ lệ chết (Càng thấp càng tốt)*")

    country_perf = df.groupby(['country', 'dev_status', 'continent']).agg({
        'response_time_hours': 'mean',
        'death_rate': 'mean',
        'event_id': 'count',
        'economic_impact_million_usd': 'sum'
    }).reset_index()
    
    country_perf = country_perf[country_perf['event_id'] > 5]

    fig_matrix = px.scatter(
        country_perf, 
        x="response_time_hours", 
        y="death_rate",
        size="event_id", 
        color="dev_status", 
        hover_name="country",
        text="country",
        log_y=True,
        title="<b>Performance Matrix: Response Speed vs. Death Rate</b>",
        labels={"response_time_hours": "Avg Response Time (Hours)", "death_rate": "Avg Death Rate (%)"}
    )
    
    fig_matrix.add_vline(x=24, line_dash="dash", line_color="red", annotation_text="Ngưỡng 24h")
    fig_matrix.update_traces(textposition='top center')
    st.plotly_chart(fig_matrix, use_container_width=True)

    st.success("**🎯 Góc lý tưởng:** Góc dưới bên trái (Nhanh & Chết ít).")

    st.markdown("---")

    # Checklist
    st.subheader("🚀 Đề xuất lộ trình hành động (Strategic Roadmap)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📅 Ngắn hạn (0-12 tháng)")
        st.checkbox("Thiết lập KPI quốc gia: **Response Time < 24h**.", value=True)
        st.checkbox("Kích hoạt quỹ thưởng **'Fast Response Bonus'**.", value=True)
        st.checkbox("Ban hành **'Mega-event Playbook'** (Model China/India).", value=True)
    
    with col2:
        st.markdown("#### 📅 Dài hạn (1-3 năm)")
        st.checkbox("Xây dựng **Regional Hubs** tại Châu Phi & Nam Á.", value=False)
        st.checkbox("Chuyển giao công nghệ vệ tinh/AI dự báo cho các nước nhỏ.", value=False)
        st.checkbox("Tái cấu trúc quy trình khẩn cấp tại các đô thị Developed.", value=False)

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🔄 Quay về Trang chủ", type="secondary", use_container_width=True):
        navigate_to('Overview')

# --- 4. ROUTING ---
if df is not None:
    # Đồng bộ Sidebar Radio với Session State
    # (Đã xử lý ở phần Sidebar đầu file)
    
    if st.session_state['current_page'] == 'Overview':
        render_overview()
    elif st.session_state['current_page'] == 'BQ1':
        render_bq1()
    elif st.session_state['current_page'] == 'BQ2':
        render_bq2()
    elif st.session_state['current_page'] == 'Conclusion':
        render_conclusion()
else:
    st.stop()
