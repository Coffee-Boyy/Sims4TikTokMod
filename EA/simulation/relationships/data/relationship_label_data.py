from __future__ import annotationsfrom relationships.global_relationship_tuning import RelationshipGlobalTuningfrom sims4.resources import get_protobuff_for_key, get_key_from_protobufffrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from Commodities_pb2 import RelationshipLabelDataUpdate
    from protocolbuffers.ResourceKey_pb2 import ResourceKey
class RelationshipLabelData:
    __slots__ = ('_label', '_icon')

    def __init__(self) -> 'None':
        self._label = None
        self._icon = None

    @property
    def label(self) -> 'str':
        return self._label

    @property
    def icon(self) -> 'ResourceKey':
        return self._icon

    def set_data(self, label:'str', icon:'ResourceKey') -> 'None':
        if label is '':
            label = None
        self._label = label
        self._icon = icon

    def destroy(self) -> 'None':
        self._label = None
        self._icon = None

    def save_data(self, relationship_label_data_msg:'RelationshipLabelDataUpdate') -> 'None':
        if self.icon is not None:
            relationship_label_data_msg.label = self.label
            icon_proto = get_protobuff_for_key(self.icon)
            relationship_label_data_msg.icon = icon_proto

    def load_data(self, relationship_label_data_msg:'RelationshipLabelDataUpdate') -> 'None':
        icon_resource = get_key_from_protobuff(relationship_label_data_msg.icon)
        if icon_resource.instance == 0:
            icon_resource = RelationshipGlobalTuning.DEFAULT_CUSTOM_RELATIONSHIP_LABEL_ICON
        self.set_data(relationship_label_data_msg.label, icon_resource)
