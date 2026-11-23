from types import SimpleNamespace

from app import ask as ask_module


def test_follow_up_questions_share_chat_history(monkeypatch, capsys):
    class FakeChat:
        def __init__(self):
            self.questions = []

        def send_message(self, question):
            self.questions.append(question)
            return SimpleNamespace(
                text=f"回答: {question}",
                usage_metadata=SimpleNamespace(prompt_token_count=1, candidates_token_count=2),
            )

    chat = FakeChat()

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.chats = SimpleNamespace(create=self.create_chat)

        def create_chat(self, model):
            assert model == ask_module.MODEL
            return chat

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("sys.argv", ["app.ask", "最初の質問"])
    follow_ups = iter(["", "続けての質問", "/exit"])

    def read_follow_up(prompt):
        assert prompt.startswith("\n[続けて質問]")
        return next(follow_ups)

    monkeypatch.setattr("builtins.input", read_follow_up)
    ask_module.main()

    assert chat.questions == ["最初の質問", "続けての質問"]
    output = capsys.readouterr().out
    assert "回答: 最初の質問" in output
    assert "回答: 続けての質問" in output
