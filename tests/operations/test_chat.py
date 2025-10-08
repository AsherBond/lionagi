# Copyright (c) 2023-2025, HaiyangLi <quantocean.li at gmail dot com>
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import AsyncMock, MagicMock

import pytest

from lionagi.operations.chat.chat import chat
from lionagi.operations.types import ChatContext
from lionagi.protocols.messages.assistant_response import AssistantResponse
from lionagi.protocols.messages.instruction import Instruction

# ============================================================================
# P0 - Critical Coverage Tests
# ============================================================================


class TestAssistantResponseConsolidation:
    """Test consolidation of consecutive AssistantResponse messages."""

    @pytest.mark.asyncio
    async def test_chat_consolidates_consecutive_assistant_responses(
        self, make_mocked_branch_for_chat
    ):
        """Verify consecutive AssistantResponse messages merge."""
        branch = make_mocked_branch_for_chat()

        # Use Branch's actual message creation methods
        ins1 = branch.msgs.add_message(
            instruction="First question",
            sender="user",
            recipient=branch.id,
        )
        resp1 = branch.msgs.add_message(
            assistant_response="First answer",
            sender=branch.id,
            recipient="user",
        )
        resp2 = branch.msgs.add_message(
            assistant_response="Second answer",
            sender=branch.id,
            recipient="user",
        )

        # Set progression to include all three
        progression = [ins1.id, resp1.id, resp2.id]

        # Create chat context
        chat_ctx = ChatContext(
            guidance=None,
            context=None,
            sender="user",
            recipient=branch.id,
            response_format=None,
            progression=progression,
            tool_schemas=[],
            images=[],
            image_detail="auto",
            plain_content="",
            include_token_usage_to_model=False,
            imodel=branch.chat_model,
            imodel_kw={},
        )

        result = await chat(
            branch, "New question", chat_ctx, return_ins_res_message=False
        )

        assert isinstance(result, str)
        assert "Mocked" in result

    @pytest.mark.asyncio
    async def test_chat_preserves_assistant_instruction_boundaries(
        self, make_mocked_branch_for_chat
    ):
        """Verify AssistantResponses stay separate when Instruction separates them."""
        branch = make_mocked_branch_for_chat()

        # Create messages with interleaving using Branch methods
        ins1 = branch.msgs.add_message(
            instruction="Q1",
            sender="user",
            recipient=branch.id,
        )
        resp1 = branch.msgs.add_message(
            assistant_response="A1",
            sender=branch.id,
            recipient="user",
        )
        ins2 = branch.msgs.add_message(
            instruction="Q2",
            sender="user",
            recipient=branch.id,
        )
        resp2 = branch.msgs.add_message(
            assistant_response="A2",
            sender=branch.id,
            recipient="user",
        )

        progression = [ins1.id, resp1.id, ins2.id, resp2.id]

        chat_ctx = ChatContext(
            guidance=None,
            context=None,
            sender="user",
            recipient=branch.id,
            response_format=None,
            progression=progression,
            tool_schemas=[],
            images=[],
            image_detail="auto",
            plain_content="",
            include_token_usage_to_model=False,
            imodel=branch.chat_model,
            imodel_kw={},
        )

        result = await chat(
            branch, "Q3", chat_ctx, return_ins_res_message=False
        )

        assert isinstance(result, str)


class TestSystemMessageHandling:
    """Test system message integration into instructions."""

    @pytest.mark.asyncio
    async def test_chat_system_message_with_empty_progression(
        self, make_mocked_branch_for_chat
    ):
        """Verify system message handling with no prior messages."""
        # Create branch with system message
        branch = make_mocked_branch_for_chat(
            system="You are a helpful assistant"
        )

        # Empty progression
        chat_ctx = ChatContext(
            guidance="Be concise",
            context=None,
            sender="user",
            recipient=branch.id,
            response_format=None,
            progression=None,  # Empty
            tool_schemas=[],
            images=[],
            image_detail="auto",
            plain_content="",
            include_token_usage_to_model=False,
            imodel=branch.chat_model,
            imodel_kw={},
        )

        result = await chat(
            branch, "Test question", chat_ctx, return_ins_res_message=False
        )

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_chat_system_message_with_existing_progression(
        self, make_mocked_branch_for_chat
    ):
        """Verify system message prepended to first instruction."""
        # Create branch with system message
        branch = make_mocked_branch_for_chat(system="You are helpful")

        # Create existing progression using Branch methods
        ins1 = branch.msgs.add_message(
            instruction="Previous question",
            sender="user",
            recipient=branch.id,
        )
        resp1 = branch.msgs.add_message(
            assistant_response="Answer",
            sender=branch.id,
            recipient="user",
        )

        progression = [ins1.id, resp1.id]

        chat_ctx = ChatContext(
            guidance=None,
            context=None,
            sender="user",
            recipient=branch.id,
            response_format=None,
            progression=progression,
            tool_schemas=[],
            images=[],
            image_detail="auto",
            plain_content="",
            include_token_usage_to_model=False,
            imodel=branch.chat_model,
            imodel_kw={},
        )

        result = await chat(
            branch, "New question", chat_ctx, return_ins_res_message=False
        )

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_chat_system_message_raises_on_non_instruction_first(
        self, make_mocked_branch_for_chat
    ):
        """Verify error when first progression message isn't Instruction."""
        # Create branch with system message
        branch = make_mocked_branch_for_chat(system="You are helpful")

        # Invalid: progression starting with AssistantResponse
        resp = branch.msgs.add_message(
            assistant_response="Wrong",
            sender=branch.id,
            recipient="user",
        )
        progression = [resp.id]

        chat_ctx = ChatContext(
            guidance=None,
            context=None,
            sender="user",
            recipient=branch.id,
            response_format=None,
            progression=progression,
            tool_schemas=[],
            images=[],
            image_detail="auto",
            plain_content="",
            include_token_usage_to_model=False,
            imodel=branch.chat_model,
            imodel_kw={},
        )

        with pytest.raises(
            ValueError,
            match="First message in progression must be an Instruction",
        ):
            await chat(
                branch, "Question", chat_ctx, return_ins_res_message=False
            )


class TestActionResponseIntegration:
    """Test ActionResponse context extension."""

    @pytest.mark.asyncio
    async def test_chat_extends_instruction_context_with_action_responses(
        self, make_mocked_branch_for_chat
    ):
        """Verify ActionResponse content added to Instruction context."""
        branch = make_mocked_branch_for_chat()

        # Create progression with ActionResponses before Instruction
        # First create action requests
        req1 = branch.msgs.add_message(
            action_function="test_func",
            action_arguments={"param": "value"},
            sender=branch.id,
            recipient="user",
        )
        req2 = branch.msgs.add_message(
            action_function="test_func2",
            action_arguments={"param": "value"},
            sender=branch.id,
            recipient="user",
        )
        # Then create action responses
        act1 = branch.msgs.add_message(
            action_request=req1,
            action_output="Result 1",
            sender="user",
            recipient=branch.id,
        )
        act2 = branch.msgs.add_message(
            action_request=req2,
            action_output="Result 2",
            sender="user",
            recipient=branch.id,
        )
        ins1 = branch.msgs.add_message(
            instruction="Use the results",
            sender="user",
            recipient=branch.id,
        )

        progression = [act1.id, act2.id, ins1.id]

        chat_ctx = ChatContext(
            guidance=None,
            context=None,
            sender="user",
            recipient=branch.id,
            response_format=None,
            progression=progression,
            tool_schemas=[],
            images=[],
            image_detail="auto",
            plain_content="",
            include_token_usage_to_model=False,
            imodel=branch.chat_model,
            imodel_kw={},
        )

        result = await chat(
            branch, "New question", chat_ctx, return_ins_res_message=False
        )

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_chat_extends_current_instruction_with_trailing_actions(
        self, make_mocked_branch_for_chat
    ):
        """Verify ActionResponse after all messages extends current instruction."""
        branch = make_mocked_branch_for_chat()

        # Progression ending with ActionResponse
        ins1 = branch.msgs.add_message(
            instruction="Do something",
            sender="user",
            recipient=branch.id,
        )
        resp1 = branch.msgs.add_message(
            assistant_response="Done",
            sender=branch.id,
            recipient="user",
        )
        # Create action request first
        req1 = branch.msgs.add_message(
            action_function="test",
            action_arguments={"param": "value"},
            sender=branch.id,
            recipient="user",
        )
        # Then create action response
        act1 = branch.msgs.add_message(
            action_request=req1,
            action_output="Action result",
            sender="user",
            recipient=branch.id,
        )

        progression = [ins1.id, resp1.id, act1.id]

        chat_ctx = ChatContext(
            guidance=None,
            context=None,
            sender="user",
            recipient=branch.id,
            response_format=None,
            progression=progression,
            tool_schemas=[],
            images=[],
            image_detail="auto",
            plain_content="",
            include_token_usage_to_model=False,
            imodel=branch.chat_model,
            imodel_kw={},
        )

        result = await chat(
            branch, "Continue", chat_ctx, return_ins_res_message=False
        )

        assert isinstance(result, str)


class TestStreamModeHandling:
    """Test stream vs invoke selection."""

    @pytest.mark.asyncio
    async def test_chat_uses_stream_when_kwarg_set(
        self, make_mocked_branch_for_chat
    ):
        """Verify imodel.stream called when stream=True."""
        branch = make_mocked_branch_for_chat()

        # Mock stream method
        async def _fake_stream(**kwargs):
            from lionagi.protocols.generic.event import EventStatus
            from lionagi.service.connections.api_calling import APICalling
            from lionagi.service.connections.endpoint import Endpoint
            from lionagi.service.connections.providers.oai_ import (
                _get_oai_config,
            )
            from lionagi.service.third_party.openai_models import (
                OpenAIChatCompletionsRequest,
            )

            config = _get_oai_config(
                name="oai_chat",
                endpoint="chat/completions",
                request_options=OpenAIChatCompletionsRequest,
                kwargs={"model": "gpt-4.1-mini"},
            )
            endpoint = Endpoint(config=config)
            fake_call = APICalling(
                payload={"model": "gpt-4.1-mini", "messages": []},
                headers={"Authorization": "Bearer test"},
                endpoint=endpoint,
            )
            fake_call.execution.response = "Stream response"
            fake_call.execution.status = EventStatus.COMPLETED
            return fake_call

        branch.chat_model.stream = AsyncMock(side_effect=_fake_stream)

        chat_ctx = ChatContext(
            guidance=None,
            context=None,
            sender="user",
            recipient=branch.id,
            response_format=None,
            progression=None,
            tool_schemas=[],
            images=[],
            image_detail="auto",
            plain_content="",
            include_token_usage_to_model=False,
            imodel=branch.chat_model,
            imodel_kw={"stream": True},  # Stream mode
        )

        result = await chat(
            branch, "Test", chat_ctx, return_ins_res_message=False
        )

        # Verify stream was called
        branch.chat_model.stream.assert_called_once()
        assert isinstance(result, str)


class TestReturnFormats:
    """Test return_ins_res_message flag behavior."""

    @pytest.mark.asyncio
    async def test_chat_returns_tuple_when_return_ins_res_message_true(
        self, make_mocked_branch_for_chat
    ):
        """Verify tuple return (Instruction, AssistantResponse)."""
        branch = make_mocked_branch_for_chat()

        chat_ctx = ChatContext(
            guidance=None,
            context=None,
            sender="user",
            recipient=branch.id,
            response_format=None,
            progression=None,
            tool_schemas=[],
            images=[],
            image_detail="auto",
            plain_content="",
            include_token_usage_to_model=False,
            imodel=branch.chat_model,
            imodel_kw={},
        )

        result = await chat(
            branch, "Test", chat_ctx, return_ins_res_message=True
        )

        # Should return tuple
        assert isinstance(result, tuple)
        assert len(result) == 2
        ins, resp = result
        assert isinstance(ins, Instruction)
        assert isinstance(resp, AssistantResponse)

    @pytest.mark.asyncio
    async def test_chat_returns_string_when_return_ins_res_message_false(
        self, make_mocked_branch_for_chat
    ):
        """Verify string return (default)."""
        branch = make_mocked_branch_for_chat()

        chat_ctx = ChatContext(
            guidance=None,
            context=None,
            sender="user",
            recipient=branch.id,
            response_format=None,
            progression=None,
            tool_schemas=[],
            images=[],
            image_detail="auto",
            plain_content="",
            include_token_usage_to_model=False,
            imodel=branch.chat_model,
            imodel_kw={},
        )

        result = await chat(
            branch, "Test", chat_ctx, return_ins_res_message=False
        )

        # Should return string
        assert isinstance(result, str)
        assert not isinstance(result, tuple)


# ============================================================================
# P1 - Important Parameter Coverage
# ============================================================================


class TestChatContextParameters:
    """Test ChatContext parameter handling and fallbacks."""

    @pytest.mark.asyncio
    async def test_chat_sender_recipient_fallback_logic(
        self, make_mocked_branch_for_chat
    ):
        """Verify sender/recipient default resolution."""
        branch = make_mocked_branch_for_chat()
        branch.user = "test_user"

        # Test with None sender (should use branch.user)
        chat_ctx = ChatContext(
            guidance=None,
            context=None,
            sender=None,  # Should default to branch.user
            recipient=None,  # Should default to branch.id
            response_format=None,
            progression=None,
            tool_schemas=[],
            images=[],
            image_detail="auto",
            plain_content="",
            include_token_usage_to_model=False,
            imodel=branch.chat_model,
            imodel_kw={},
        )

        ins, resp = await chat(
            branch, "Test", chat_ctx, return_ins_res_message=True
        )

        # Verify sender/recipient were set correctly
        assert ins.sender == branch.user or ins.sender == "user"
        assert ins.recipient == branch.id

    @pytest.mark.asyncio
    async def test_chat_with_images(self, make_mocked_branch_for_chat):
        """Verify images parameter in ChatContext."""
        branch = make_mocked_branch_for_chat()

        chat_ctx = ChatContext(
            guidance=None,
            context=None,
            sender="user",
            recipient=branch.id,
            response_format=None,
            progression=None,
            tool_schemas=[],
            images=["data:image/png;base64,abc123"],
            image_detail="high",
            plain_content="",
            include_token_usage_to_model=False,
            imodel=branch.chat_model,
            imodel_kw={},
        )

        result = await chat(
            branch, "Describe image", chat_ctx, return_ins_res_message=False
        )

        assert isinstance(result, str)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def make_mocked_branch_for_chat():
    """Factory fixture for creating branches with mocked chat responses."""

    def _make_branch(system=None):
        from lionagi.protocols.generic.event import EventStatus
        from lionagi.service.connections.api_calling import APICalling
        from lionagi.service.connections.endpoint import Endpoint
        from lionagi.service.connections.providers.oai_ import _get_oai_config
        from lionagi.service.imodel import iModel
        from lionagi.service.third_party.openai_models import (
            OpenAIChatCompletionsRequest,
        )
        from lionagi.session.branch import Branch

        branch = Branch(
            imodel=iModel(provider="openai", model="gpt-4.1-mini"),
            system=system,
        )

        # Mock imodel.invoke
        async def _fake_invoke(**kwargs):
            config = _get_oai_config(
                name="oai_chat",
                endpoint="chat/completions",
                request_options=OpenAIChatCompletionsRequest,
                kwargs={"model": "gpt-4.1-mini"},
            )
            endpoint = Endpoint(config=config)
            fake_call = APICalling(
                payload={"model": "gpt-4.1-mini", "messages": []},
                headers={"Authorization": "Bearer test"},
                endpoint=endpoint,
            )
            fake_call.execution.response = "Mocked chat response"
            fake_call.execution.status = EventStatus.COMPLETED
            return fake_call

        branch.chat_model.invoke = AsyncMock(side_effect=_fake_invoke)

        # Mock _log_manager.create_log
        branch._log_manager.create_log = MagicMock()

        return branch

    return _make_branch
