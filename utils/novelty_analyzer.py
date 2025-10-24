"""
新規性・進歩性分析ユーティリティ

発明アイデアと公知文献を比較分析し、新規性・進歩性の評価および
追加アイデア・クレーム提案を行います。
"""

from typing import Dict, List, Optional
from openai import OpenAI
import json
import os


class NoveltyAnalyzer:
    """新規性・進歩性を分析するクラス"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo"):
        """
        初期化

        Args:
            api_key: OpenAI APIキー
            model: 使用するモデル名
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def analyze_novelty_and_inventive_step(
        self,
        invention_idea: Dict[str, str],
        prior_arts: List[Dict[str, str]]
    ) -> Dict:
        """
        新規性・進歩性の総合分析

        Args:
            invention_idea: 発明アイデア
                - technical_field: 技術分野
                - problem: 解決したい課題
                - solution: 解決手段
                - effect: 効果
            prior_arts: 公知文献リスト
                - filename: ファイル名
                - text_content: テキスト内容

        Returns:
            Dict: 分析結果
        """
        # 各公知文献との比較分析
        prior_art_comparisons = []
        for prior_art in prior_arts:
            comparison = self._compare_with_prior_art(invention_idea, prior_art)
            prior_art_comparisons.append(comparison)

        # 総合評価
        overall_evaluation = self._evaluate_overall(
            invention_idea,
            prior_art_comparisons
        )

        # 新規性・進歩性がない場合は追加アイデアを提案
        additional_ideas = []
        if not overall_evaluation["novelty"]["judgment"] or \
           not overall_evaluation["inventive_step"]["judgment"]:
            additional_ideas = self._generate_additional_ideas(
                invention_idea,
                prior_art_comparisons,
                overall_evaluation
            )

        # クレーム提案
        claim_proposals = self._generate_claim_proposals(
            invention_idea,
            overall_evaluation,
            additional_ideas
        )

        return {
            "novelty": overall_evaluation["novelty"],
            "inventive_step": overall_evaluation["inventive_step"],
            "prior_art_comparison": prior_art_comparisons,
            "additional_ideas": additional_ideas,
            "claim_proposals": claim_proposals,
            "analysis_summary": self._create_analysis_summary(
                overall_evaluation,
                prior_art_comparisons,
                additional_ideas,
                claim_proposals
            )
        }

    def _compare_with_prior_art(
        self,
        invention_idea: Dict[str, str],
        prior_art: Dict[str, str]
    ) -> Dict:
        """
        発明アイデアと公知文献を比較

        Args:
            invention_idea: 発明アイデア
            prior_art: 公知文献

        Returns:
            Dict: 比較結果
        """
        prompt = f"""あなたは特許審査官です。以下の発明アイデアと公知文献を比較分析してください。

【発明アイデア】
技術分野: {invention_idea['technical_field']}
解決したい課題: {invention_idea['problem']}
解決手段: {invention_idea['solution']}
効果: {invention_idea['effect']}

【公知文献】
{prior_art['text_content'][:8000]}

以下の形式のJSONで出力してください:
{{
    "similarities": ["類似点1", "類似点2", ...],
    "differences": ["相違点1", "相違点2", ...],
    "technical_significance": "相違点の技術的意義についての説明"
}}

類似点と相違点は具体的かつ簡潔に記載してください。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "あなたは特許審査の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return {
                "prior_art_filename": prior_art["filename"],
                "similarities": result.get("similarities", []),
                "differences": result.get("differences", []),
                "technical_significance": result.get("technical_significance", "")
            }
        except Exception as e:
            return {
                "prior_art_filename": prior_art["filename"],
                "similarities": [],
                "differences": [],
                "technical_significance": f"エラー: {str(e)}"
            }

    def _evaluate_overall(
        self,
        invention_idea: Dict[str, str],
        prior_art_comparisons: List[Dict]
    ) -> Dict:
        """
        総合的な新規性・進歩性評価

        Args:
            invention_idea: 発明アイデア
            prior_art_comparisons: 公知文献との比較結果リスト

        Returns:
            Dict: 評価結果
        """
        # 比較結果のサマリーを作成
        comparison_summary = ""
        for i, comp in enumerate(prior_art_comparisons, 1):
            comparison_summary += f"\n【公知文献{i}: {comp['prior_art_filename']}】\n"
            comparison_summary += f"類似点: {', '.join(comp['similarities'][:3])}\n"
            comparison_summary += f"相違点: {', '.join(comp['differences'][:3])}\n"

        prompt = f"""あなたは特許審査官です。特許法第29条に基づき、以下の発明アイデアの新規性・進歩性を評価してください。

【発明アイデア】
技術分野: {invention_idea['technical_field']}
解決したい課題: {invention_idea['problem']}
解決手段: {invention_idea['solution']}
効果: {invention_idea['effect']}

【公知文献との比較結果】
{comparison_summary}

以下の基準で評価してください:
- 新規性: すべての公知文献に対して相違点があるか
- 進歩性: 相違点が当業者にとって容易に想到できないか、または顕著な効果があるか

以下の形式のJSONで出力してください:
{{
    "novelty": {{
        "judgment": true/false,
        "reason": "判定理由の詳細な説明"
    }},
    "inventive_step": {{
        "judgment": true/false,
        "reason": "判定理由の詳細な説明"
    }}
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "あなたは特許審査の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            return {
                "novelty": {
                    "judgment": False,
                    "reason": f"評価エラー: {str(e)}"
                },
                "inventive_step": {
                    "judgment": False,
                    "reason": f"評価エラー: {str(e)}"
                }
            }

    def _generate_additional_ideas(
        self,
        invention_idea: Dict[str, str],
        prior_art_comparisons: List[Dict],
        overall_evaluation: Dict
    ) -> List[Dict]:
        """
        追加の発明アイデアを提案

        Args:
            invention_idea: 発明アイデア
            prior_art_comparisons: 公知文献との比較結果
            overall_evaluation: 総合評価

        Returns:
            List[Dict]: 追加アイデアリスト
        """
        comparison_summary = ""
        for i, comp in enumerate(prior_art_comparisons, 1):
            comparison_summary += f"\n【公知文献{i}: {comp['prior_art_filename']}】\n"
            comparison_summary += f"相違点: {', '.join(comp['differences'])}\n"

        prompt = f"""あなたは発明支援コンサルタントです。以下の発明アイデアに新規性・進歩性を持たせるための追加要素を提案してください。

【現在の発明アイデア】
技術分野: {invention_idea['technical_field']}
解決したい課題: {invention_idea['problem']}
解決手段: {invention_idea['solution']}
効果: {invention_idea['effect']}

【評価結果】
新規性: {'あり' if overall_evaluation['novelty']['judgment'] else 'なし'}
理由: {overall_evaluation['novelty']['reason']}

進歩性: {'あり' if overall_evaluation['inventive_step']['judgment'] else 'なし'}
理由: {overall_evaluation['inventive_step']['reason']}

【公知文献との比較】
{comparison_summary}

新規性・進歩性を確保するための追加アイデアを3〜5案提案してください。

以下の形式のJSONで出力してください:
{{
    "ideas": [
        {{
            "idea_number": 1,
            "description": "追加すべき技術的特徴の具体的説明",
            "rationale": "なぜこの追加によって新規性・進歩性が確保できるか",
            "implementation_difficulty": "低/中/高",
            "differentiation_point": "公知文献との差別化ポイント"
        }},
        ...
    ]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "あなたは発明支援の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("ideas", [])
        except Exception as e:
            return [{
                "idea_number": 1,
                "description": f"エラーが発生しました: {str(e)}",
                "rationale": "",
                "implementation_difficulty": "不明",
                "differentiation_point": ""
            }]

    def _generate_claim_proposals(
        self,
        invention_idea: Dict[str, str],
        overall_evaluation: Dict,
        additional_ideas: List[Dict]
    ) -> List[Dict]:
        """
        クレーム案を提案

        Args:
            invention_idea: 発明アイデア
            overall_evaluation: 総合評価
            additional_ideas: 追加アイデアリスト

        Returns:
            List[Dict]: クレーム提案リスト
        """
        additional_context = ""
        if additional_ideas:
            additional_context = "\n【追加アイデア】\n"
            for idea in additional_ideas[:3]:
                additional_context += f"- {idea['description']}\n"

        prompt = f"""あなたは弁理士です。以下の発明について、特許請求の範囲（クレーム）の文言案を作成してください。

【発明アイデア】
技術分野: {invention_idea['technical_field']}
解決したい課題: {invention_idea['problem']}
解決手段: {invention_idea['solution']}
効果: {invention_idea['effect']}
{additional_context}

独立請求項形式で、3〜5パターンのクレーム案を作成してください。
上位概念から下位概念まで、保護範囲の異なる複数のバリエーションを提案してください。

以下の形式のJSONで出力してください:
{{
    "claims": [
        {{
            "claim_number": 1,
            "claim_text": "【請求項1】...",
            "scope": "上位概念/中位概念/下位概念",
            "key_features": ["重要な技術的特徴1", "重要な技術的特徴2", ...]
        }},
        ...
    ]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "あなたは特許クレーム作成の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("claims", [])
        except Exception as e:
            return [{
                "claim_number": 1,
                "claim_text": f"エラーが発生しました: {str(e)}",
                "scope": "不明",
                "key_features": []
            }]

    def _create_analysis_summary(
        self,
        overall_evaluation: Dict,
        prior_art_comparisons: List[Dict],
        additional_ideas: List[Dict],
        claim_proposals: List[Dict]
    ) -> str:
        """
        分析結果のサマリーを作成

        Args:
            overall_evaluation: 総合評価
            prior_art_comparisons: 公知文献比較結果
            additional_ideas: 追加アイデア
            claim_proposals: クレーム提案

        Returns:
            str: サマリーテキスト
        """
        summary = "# 特許新規性分析レポート\n\n"

        summary += "## 総合評価\n\n"
        summary += f"**新規性**: {'✓ あり' if overall_evaluation['novelty']['judgment'] else '✗ なし'}\n"
        summary += f"- {overall_evaluation['novelty']['reason']}\n\n"
        summary += f"**進歩性**: {'✓ あり' if overall_evaluation['inventive_step']['judgment'] else '✗ なし'}\n"
        summary += f"- {overall_evaluation['inventive_step']['reason']}\n\n"

        summary += f"## 公知文献との比較 ({len(prior_art_comparisons)}件)\n\n"
        for i, comp in enumerate(prior_art_comparisons, 1):
            summary += f"### {i}. {comp['prior_art_filename']}\n\n"
            summary += "**類似点**:\n"
            for sim in comp['similarities']:
                summary += f"- {sim}\n"
            summary += "\n**相違点**:\n"
            for diff in comp['differences']:
                summary += f"- {diff}\n"
            summary += f"\n**技術的意義**: {comp['technical_significance']}\n\n"

        if additional_ideas:
            summary += f"## 追加アイデア提案 ({len(additional_ideas)}件)\n\n"
            for idea in additional_ideas:
                summary += f"### アイデア {idea['idea_number']}\n"
                summary += f"**内容**: {idea['description']}\n\n"
                summary += f"**根拠**: {idea['rationale']}\n\n"
                summary += f"**実装難易度**: {idea['implementation_difficulty']}\n\n"
                summary += f"**差別化ポイント**: {idea['differentiation_point']}\n\n"

        summary += f"## クレーム提案 ({len(claim_proposals)}件)\n\n"
        for claim in claim_proposals:
            summary += f"### クレーム案 {claim['claim_number']} ({claim['scope']})\n"
            summary += f"{claim['claim_text']}\n\n"
            summary += "**重要な技術的特徴**:\n"
            for feature in claim['key_features']:
                summary += f"- {feature}\n"
            summary += "\n"

        return summary
