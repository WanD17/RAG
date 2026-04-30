import uuid
from collections import OrderedDict

_MAX_CONVERSATIONS = 1000
_MAX_MESSAGES = 50       # total messages per conversation
_WINDOW_TURNS = 6        # last N turns injected into prompt
_MAX_ASSISTANT_CHARS = 1200


class ConversationManager:
    def __init__(self) -> None:
        self._store: OrderedDict[uuid.UUID, list[dict]] = OrderedDict()

    def get_history(self, conversation_id: uuid.UUID) -> list[dict]:
        """Return last WINDOW_TURNS turns as [{role, content}, ...]."""
        messages = self._store.get(conversation_id, [])
        return messages[-(2 * _WINDOW_TURNS):]

    def add_turn(self, conversation_id: uuid.UUID, question: str, answer: str) -> None:
        if conversation_id not in self._store:
            if len(self._store) >= _MAX_CONVERSATIONS:
                self._store.popitem(last=False)
            self._store[conversation_id] = []
        messages = self._store[conversation_id]
        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": answer[:_MAX_ASSISTANT_CHARS]})
        if len(messages) > _MAX_MESSAGES:
            self._store[conversation_id] = messages[-_MAX_MESSAGES:]
        self._store.move_to_end(conversation_id)

    def create(self) -> uuid.UUID:
        conv_id = uuid.uuid4()
        if len(self._store) >= _MAX_CONVERSATIONS:
            self._store.popitem(last=False)
        self._store[conv_id] = []
        return conv_id


conversation_manager = ConversationManager()
