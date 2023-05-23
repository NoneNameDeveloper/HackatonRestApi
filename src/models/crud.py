from . import Conversation, ConversationStart


def get_conversation(id_: str):
    """
    начинался ли такой диалог
    """
    return ConversationStart.get_or_none(ConversationStart.conversation_id == id_)


def get_conversation_data(id_: str):
    """
    получение всех записей по данному диалогу
    """
    return Conversation.get_or_none(Conversation.conversation_id == id_)
