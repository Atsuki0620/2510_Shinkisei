"""
特許新規性分析支援システム（新規性くん）

発明アイデアと公知文献を比較し、新規性・進歩性を評価するStreamlitアプリケーション
"""

import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime
from utils.pdf_processor import PDFProcessor, format_file_size
from utils.novelty_analyzer import NoveltyAnalyzer

# 環境変数の読み込み
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="特許新規性分析システム",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .success-box {
        padding: 20px;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        margin: 10px 0;
    }
    .warning-box {
        padding: 20px;
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        margin: 10px 0;
    }
    .danger-box {
        padding: 20px;
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """セッション状態の初期化"""
    if 'uploaded_pdfs' not in st.session_state:
        st.session_state.uploaded_pdfs = []
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'technical_field' not in st.session_state:
        st.session_state.technical_field = ""
    if 'problem' not in st.session_state:
        st.session_state.problem = ""
    if 'solution' not in st.session_state:
        st.session_state.solution = ""
    if 'effect' not in st.session_state:
        st.session_state.effect = ""


def display_header():
    """ヘッダー表示"""
    st.title("🔍 特許新規性分析システム（新規性くん）")
    st.markdown("---")
    st.markdown("""
    発明アイデアと公知文献を比較分析し、新規性・進歩性を評価します。
    追加のアイデア提案やクレーム案も自動生成します。
    """)


def input_invention_idea():
    """発明アイデア入力セクション"""
    st.header("📝 発明アイデア入力")

    with st.expander("入力ガイド", expanded=False):
        st.markdown("""
        **技術分野**: 発明が属する技術分野（例: 情報処理、機械工学、電気回路）

        **解決したい課題**: 従来技術の問題点や解決すべき課題を明確に記載

        **解決手段**: 発明の具体的な内容・仕組み・特徴を詳しく記載

        **効果**: 発明によって得られる効果・利点を具体的に記載
        """)

    col1, col2 = st.columns(2)

    with col1:
        technical_field = st.text_area(
            "技術分野 *",
            value=st.session_state.technical_field,
            height=100,
            placeholder="例: AI・機械学習を用いた画像認識技術",
            help="発明が属する技術分野を入力してください"
        )
        st.session_state.technical_field = technical_field

        solution = st.text_area(
            "解決手段 *",
            value=st.session_state.solution,
            height=200,
            placeholder="例: ニューラルネットワークの構造を改良し、特徴抽出層を追加することで...",
            help="発明の具体的な内容・仕組みを入力してください"
        )
        st.session_state.solution = solution

    with col2:
        problem = st.text_area(
            "解決したい課題 *",
            value=st.session_state.problem,
            height=100,
            placeholder="例: 従来の画像認識では小さな物体の検出精度が低い",
            help="解決すべき課題を入力してください"
        )
        st.session_state.problem = problem

        effect = st.text_area(
            "効果 *",
            value=st.session_state.effect,
            height=200,
            placeholder="例: 小さな物体の検出精度が従来比30%向上し、処理速度も改善される",
            help="発明によって得られる効果を入力してください"
        )
        st.session_state.effect = effect

    # クリアボタン
    if st.button("入力内容をクリア", type="secondary"):
        st.session_state.technical_field = ""
        st.session_state.problem = ""
        st.session_state.solution = ""
        st.session_state.effect = ""
        st.rerun()


def upload_prior_art_pdfs():
    """公知文献PDF読み込みセクション"""
    st.header("📄 公知文献PDFアップロード")

    st.markdown("""
    特許明細書などの公知文献をPDF形式でアップロードしてください。
    - 最大10ファイルまで
    - 1ファイルあたり20MBまで
    - テキストPDFのみ対応（OCR非対応）
    """)

    uploaded_files = st.file_uploader(
        "PDFファイルを選択",
        type=['pdf'],
        accept_multiple_files=True,
        help="複数ファイルを一度に選択できます"
    )

    if uploaded_files:
        if len(uploaded_files) > 10:
            st.error("❌ アップロードできるファイルは最大10個までです")
        else:
            # PDFを処理
            processor = PDFProcessor(max_file_size_mb=20)

            # 新しくアップロードされたファイルを処理
            new_pdfs = []
            for uploaded_file in uploaded_files:
                # 既存のリストに同名ファイルがなければ処理
                if not any(pdf['filename'] == uploaded_file.name
                          for pdf in st.session_state.uploaded_pdfs):
                    with st.spinner(f"{uploaded_file.name} を処理中..."):
                        result = processor.extract_text_from_pdf(uploaded_file)
                        if result['success']:
                            new_pdfs.append({
                                'filename': result['filename'],
                                'file_size': result['file_size'],
                                'page_count': result['page_count'],
                                'text_content': result['text_content']
                            })
                        else:
                            st.error(f"❌ {result['filename']}: {result['error']}")

            # 新規PDFを追加
            if new_pdfs:
                st.session_state.uploaded_pdfs.extend(new_pdfs)
                st.success(f"✓ {len(new_pdfs)}件のPDFを読み込みました")

    # アップロード済みファイルリストの表示
    if st.session_state.uploaded_pdfs:
        st.markdown("### アップロード済みファイル")

        for idx, pdf in enumerate(st.session_state.uploaded_pdfs):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.text(f"📄 {pdf['filename']}")
            with col2:
                st.text(f"{format_file_size(pdf['file_size'])}")
            with col3:
                st.text(f"{pdf['page_count']}ページ")
            with col4:
                if st.button("🗑️", key=f"delete_{idx}"):
                    st.session_state.uploaded_pdfs.pop(idx)
                    st.rerun()


def validate_inputs():
    """入力内容の検証"""
    if not st.session_state.technical_field.strip():
        return False, "技術分野を入力してください"
    if not st.session_state.problem.strip():
        return False, "解決したい課題を入力してください"
    if not st.session_state.solution.strip():
        return False, "解決手段を入力してください"
    if not st.session_state.effect.strip():
        return False, "効果を入力してください"
    if not st.session_state.uploaded_pdfs:
        return False, "少なくとも1つの公知文献PDFをアップロードしてください"

    return True, ""


def execute_analysis():
    """分析実行セクション"""
    st.markdown("---")

    col1, col2, col3 = st.columns([2, 1, 2])

    with col2:
        if st.button("🚀 分析実行", type="primary", use_container_width=True):
            # 入力検証
            is_valid, error_message = validate_inputs()
            if not is_valid:
                st.error(f"❌ {error_message}")
                return

            # APIキーのチェック
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                st.error("❌ OpenAI APIキーが設定されていません。.envファイルを確認してください。")
                return

            # 分析実行
            with st.spinner("分析中... 数分かかる場合があります"):
                try:
                    analyzer = NoveltyAnalyzer(api_key=api_key)

                    invention_idea = {
                        'technical_field': st.session_state.technical_field,
                        'problem': st.session_state.problem,
                        'solution': st.session_state.solution,
                        'effect': st.session_state.effect
                    }

                    prior_arts = [
                        {
                            'filename': pdf['filename'],
                            'text_content': pdf['text_content']
                        }
                        for pdf in st.session_state.uploaded_pdfs
                    ]

                    result = analyzer.analyze_novelty_and_inventive_step(
                        invention_idea,
                        prior_arts
                    )

                    st.session_state.analysis_result = result
                    st.success("✓ 分析が完了しました！")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ 分析中にエラーが発生しました: {str(e)}")


def display_analysis_results():
    """分析結果表示セクション"""
    if st.session_state.analysis_result is None:
        return

    result = st.session_state.analysis_result

    st.markdown("---")
    st.header("📊 分析結果")

    # 評価サマリー
    st.subheader("総合評価")
    col1, col2 = st.columns(2)

    with col1:
        novelty_judgment = result['novelty']['judgment']
        if novelty_judgment:
            st.markdown('<div class="success-box"><h3>✓ 新規性: あり</h3></div>',
                       unsafe_allow_html=True)
        else:
            st.markdown('<div class="danger-box"><h3>✗ 新規性: なし</h3></div>',
                       unsafe_allow_html=True)
        st.write(result['novelty']['reason'])

    with col2:
        inventive_judgment = result['inventive_step']['judgment']
        if inventive_judgment:
            st.markdown('<div class="success-box"><h3>✓ 進歩性: あり</h3></div>',
                       unsafe_allow_html=True)
        else:
            st.markdown('<div class="danger-box"><h3>✗ 進歩性: なし</h3></div>',
                       unsafe_allow_html=True)
        st.write(result['inventive_step']['reason'])

    # タブ表示
    tabs = st.tabs(["📋 公知文献比較", "📈 評価詳細", "💡 提案内容", "📄 レポート"])

    # タブ1: 公知文献比較
    with tabs[0]:
        st.subheader(f"公知文献との比較 ({len(result['prior_art_comparison'])}件)")

        for i, comp in enumerate(result['prior_art_comparison'], 1):
            with st.expander(f"📄 {i}. {comp['prior_art_filename']}", expanded=(i == 1)):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**類似点**")
                    for sim in comp['similarities']:
                        st.write(f"- {sim}")

                with col2:
                    st.markdown("**相違点**")
                    for diff in comp['differences']:
                        st.write(f"- {diff}")

                st.markdown("**技術的意義**")
                st.write(comp['technical_significance'])

    # タブ2: 評価詳細
    with tabs[1]:
        st.subheader("新規性・進歩性の詳細評価")

        st.markdown("### 新規性評価")
        st.write(f"**判定**: {'✓ あり' if result['novelty']['judgment'] else '✗ なし'}")
        st.write(f"**理由**: {result['novelty']['reason']}")

        st.markdown("---")

        st.markdown("### 進歩性評価")
        st.write(f"**判定**: {'✓ あり' if result['inventive_step']['judgment'] else '✗ なし'}")
        st.write(f"**理由**: {result['inventive_step']['reason']}")

    # タブ3: 提案内容
    with tabs[2]:
        if result['additional_ideas']:
            st.subheader(f"追加アイデア提案 ({len(result['additional_ideas'])}件)")
            st.info("新規性・進歩性を確保するための追加要素を提案します")

            for idea in result['additional_ideas']:
                with st.expander(f"💡 アイデア {idea['idea_number']}", expanded=True):
                    st.markdown(f"**内容**")
                    st.write(idea['description'])

                    st.markdown(f"**根拠**")
                    st.write(idea['rationale'])

                    col1, col2 = st.columns(2)
                    with col1:
                        difficulty_color = {
                            '低': '🟢',
                            '中': '🟡',
                            '高': '🔴'
                        }.get(idea['implementation_difficulty'], '⚪')
                        st.markdown(f"**実装難易度**: {difficulty_color} {idea['implementation_difficulty']}")

                    with col2:
                        st.markdown(f"**差別化ポイント**")
                        st.write(idea['differentiation_point'])

        st.markdown("---")

        if result['claim_proposals']:
            st.subheader(f"クレーム提案 ({len(result['claim_proposals'])}件)")

            for claim in result['claim_proposals']:
                with st.expander(
                    f"📜 クレーム案 {claim['claim_number']} ({claim['scope']})",
                    expanded=True
                ):
                    st.markdown("**クレーム文言**")
                    st.text_area(
                        "",
                        value=claim['claim_text'],
                        height=150,
                        key=f"claim_{claim['claim_number']}",
                        label_visibility="collapsed"
                    )

                    st.markdown("**重要な技術的特徴**")
                    for feature in claim['key_features']:
                        st.write(f"- {feature}")

    # タブ4: レポート
    with tabs[3]:
        st.subheader("分析レポート")
        st.markdown(result['analysis_summary'])

        # ダウンロードボタン
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            # Markdown形式でダウンロード
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_md = f"特許分析レポート_{timestamp}.md"

            st.download_button(
                label="📥 Markdownでダウンロード",
                data=result['analysis_summary'],
                file_name=filename_md,
                mime="text/markdown"
            )

        with col2:
            # テキスト形式でダウンロード
            filename_txt = f"特許分析レポート_{timestamp}.txt"

            st.download_button(
                label="📥 テキストでダウンロード",
                data=result['analysis_summary'],
                file_name=filename_txt,
                mime="text/plain"
            )


def display_sidebar():
    """サイドバー表示"""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/4CAF50/FFFFFF?text=新規性くん",
                use_container_width=True)

        st.markdown("---")
        st.markdown("### ℹ️ システム情報")
        st.markdown("""
        **バージョン**: 1.0.0

        **使用モデル**: GPT-4 Turbo

        **開発**: 特許分析支援システム
        """)

        st.markdown("---")
        st.markdown("### 📖 使い方")
        st.markdown("""
        1. 発明アイデアを入力
        2. 公知文献PDFをアップロード
        3. 分析実行ボタンをクリック
        4. 結果を確認・ダウンロード
        """)

        st.markdown("---")
        st.markdown("### ⚠️ 注意事項")
        st.markdown("""
        - テキストPDFのみ対応
        - 最大10ファイルまで
        - 分析には数分かかります
        - OpenAI APIキーが必要
        """)

        if st.session_state.uploaded_pdfs or st.session_state.analysis_result:
            st.markdown("---")
            if st.button("🔄 すべてリセット", use_container_width=True):
                st.session_state.clear()
                st.rerun()


def main():
    """メイン処理"""
    # 初期化
    initialize_session_state()

    # サイドバー
    display_sidebar()

    # ヘッダー
    display_header()

    # 発明アイデア入力
    input_invention_idea()

    st.markdown("---")

    # 公知文献アップロード
    upload_prior_art_pdfs()

    # 分析実行
    execute_analysis()

    # 結果表示
    display_analysis_results()


if __name__ == "__main__":
    main()
