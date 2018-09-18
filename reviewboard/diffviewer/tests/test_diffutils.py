from django.test.client import RequestFactory
    get_original_file,


class GetOriginalFileTests(TestCase):
    """Unit tests for get_original_file."""

    fixtures = ['test_scmtools']

    def test_empty_parent_diff(self):
        """Testing get_original_file with an empty parent diff"""
        parent_diff = (
            b'diff --git a/empty b/empty\n'
            b'new file mode 100644\n'
            b'index 0000000..e69de29\n'
            b'\n'
        )

        diff = (
            b'diff --git a/empty b/empty\n'
            b'index e69de29..0e4b0c7 100644\n'
            b'--- a/empty\n'
            b'+++ a/empty\n'
            b'@@ -0,0 +1 @@\n'
            b'+abc123\n'
        )

        repository = self.create_repository(tool_name='Git')
        diffset = self.create_diffset(repository=repository)
        filediff = FileDiff.objects.create(
            diffset=diffset,
            source_file='empty',
            source_revision=PRE_CREATION,
            dest_file='empty',
            dest_detail='0e4b0c7')
        filediff.parent_diff = parent_diff
        filediff.diff = diff
        filediff.save()

        request_factory = RequestFactory()

        # 1 query for fetching the ``FileDiff.parent_diff_hash`` and 1 for
        # saving the object.
        with self.assertNumQueries(2):
            orig = get_original_file(
                filediff=filediff,
                request=request_factory.get('/'),
                encoding_list=['ascii'])

        self.assertEqual(orig, b'')

        # Refresh the object from the database with the parent diff attached
        # and then verify that re-calculating the original file does not cause
        # additional queries.
        filediff = (
            FileDiff.objects
            .filter(pk=filediff.pk)
            .select_related('parent_diff_hash')
            .first()
        )

        with self.assertNumQueries(0):
            orig = get_original_file(
                filediff=filediff,
                request=request_factory.get('/'),
                encoding_list=['ascii'])