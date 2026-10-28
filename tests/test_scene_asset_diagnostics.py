import copy
import unittest

import scene_assets as assets
from tests.scene_asset_fixtures import glb_parts, pack_glb
from tests.test_scene_assets import geometry


COMPLEXITY_ERROR = 'GLB 모델이 너무 복잡해 가져올 수 없습니다. 더 단순한 정적 GLB 파일을 선택하세요.'
MALFORMED_ERROR = '지원하지 않거나 손상된 GLB 모델입니다.'


class SceneAssetDiagnosticsTest(unittest.TestCase):
    def assert_rejected(self, raw, message):
        with self.assertRaises(ValueError) as failure:
            assets.validate_glb(raw)
        self.assertEqual(str(failure.exception), message)

    def test_malformed_counts_keep_format_error_and_positive_overflow_explains_recovery(self):
        document, binary = glb_parts(geometry())
        for count in (True, False, -1, 0, 1.5, '300001', None, [], {}):
            with self.subTest(count=count):
                document['accessors'][0]['count'] = count
                self.assert_rejected(pack_glb(document, binary), MALFORMED_ERROR)
        for count in (assets.MAX_TRIANGLES * 3 + 1, 777780, 2**40):
            with self.subTest(count=count):
                document['accessors'][0]['count'] = count
                self.assert_rejected(pack_glb(document, binary), COMPLEXITY_ERROR)

    def test_supported_accessor_count_with_missing_bytes_still_reports_format_error(self):
        document, binary = glb_parts(geometry())
        document['accessors'][1]['count'] = assets.MAX_TRIANGLES * 3
        self.assert_rejected(pack_glb(document, binary), MALFORMED_ERROR)

    def test_scalar_budget_boundary_and_overflow_without_changing_limits(self):
        document, binary = glb_parts(geometry(assets.MAX_VERTICES, assets.MAX_TRIANGLES))
        position, indices = document['accessors']
        document['accessors'] = [copy.deepcopy(position) for _ in range(4)] + [indices]
        self.assertEqual(sum(a['count'] * assets._DIMENSIONS[a['type']] for a in document['accessors']), assets.MAX_ACCESSOR_VALUES)
        _, decoded = assets._views_and_accessors(document, binary)
        self.assertEqual(len(decoded), 5)
        document['accessors'].append(copy.deepcopy(position))
        self.assert_rejected(pack_glb(document, binary), COMPLEXITY_ERROR)

    def test_mesh_and_instance_aggregate_limits_have_the_same_recovery(self):
        for vertices, triangles in ((assets.MAX_VERTICES // 2 + 1, 1), (3, assets.MAX_TRIANGLES // 2 + 1)):
            for duplicate_mesh in (False, True):
                with self.subTest(vertices=vertices, triangles=triangles, duplicate_mesh=duplicate_mesh):
                    document, binary = glb_parts(geometry(vertices, triangles))
                    if duplicate_mesh:
                        document['meshes'].append(copy.deepcopy(document['meshes'][0]))
                    document['nodes'] = [{'mesh': 0}, {'mesh': int(duplicate_mesh)}]
                    document['scenes'][0]['nodes'] = [0, 1]
                    self.assert_rejected(pack_glb(document, binary), COMPLEXITY_ERROR)


if __name__ == '__main__':
    unittest.main()
