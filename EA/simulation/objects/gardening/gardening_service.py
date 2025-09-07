from __future__ import annotationsfrom _collections import defaultdictfrom sims4.service_manager import Serviceimport sims4.geometryfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from Math_pb2 import Vector3
    from objects.game_object import GameObject
class GardeningService(Service):

    def __init__(self, *args, **kwargs) -> 'None':
        super().__init__(*args, **kwargs)
        self._gardening_quadtrees = defaultdict(sims4.geometry.QuadTree)

    def add_gardening_object(self, obj:'GameObject') -> 'None':
        quadtree = self._gardening_quadtrees[obj.level]
        quadtree.insert(obj, obj.get_bounding_box())

    def get_gardening_objects(self, *, level, center, radius) -> 'List[GameObject]':
        results = []
        if level in self._gardening_quadtrees:
            if isinstance(center, sims4.math.Vector3):
                center = sims4.math.Vector2(center.x, center.z)
            bounds = sims4.geometry.QtCircle(center, radius)
            quadtree = self._gardening_quadtrees[level]
            results = quadtree.query(bounds)

        def _distance_from_center(position:'Vector3') -> 'float':
            position = sims4.math.Vector2(position.x, position.z)
            return (position - center).magnitude_squared()

        results.sort(key=lambda x: _distance_from_center(x.position))
        return results

    def move_gardening_object(self, obj:'GameObject') -> 'None':
        for quadtree in self._gardening_quadtrees.values():
            quadtree.remove(obj)
        self.add_gardening_object(obj)

    def remove_gardening_object(self, obj:'GameObject') -> 'None':
        quadtree = self._gardening_quadtrees[obj.level]
        quadtree.remove(obj)
