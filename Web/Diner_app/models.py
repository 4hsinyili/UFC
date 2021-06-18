# import pprint
# import time
from django.db import models
from User_app.models import CustomUser
# Create your models here.


class NoteqManager(models.Manager):
    def add_noteq(self, user, uuid_ue, uuid_fp, uuid_gm):
        noteq_sqlrecord = self.create(
            user=user,
            uuid_ue=uuid_ue,
            uuid_fp=uuid_fp,
            uuid_gm=uuid_gm,
            count=1)
        return noteq_sqlrecord


class Noteq(models.Model):
    uuid_ue = models.CharField(max_length=40, default=None, blank=True, null=True)
    uuid_fp = models.CharField(max_length=40, default=None, blank=True, null=True)
    uuid_gm = models.CharField(max_length=40, default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    count = models.IntegerField(default=0)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    objects = models.Manager()
    manager = NoteqManager()

    def __str__(self):
        return f'user: {self.user.email} report {self.uuid_ue} ,{self.uuid_fp} ,{self.uuid_gm} not eq'


class FavoritesManager(models.Manager):
    def update_favorite(self, user, uuid_ue, uuid_fp, activate):
        favorite_sqlrecord = self.update_or_create(
            user=user,
            uuid_ue=uuid_ue,
            uuid_fp=uuid_fp,
            defaults={'activate': activate})
        return favorite_sqlrecord

    def get_favorites(self, user, offset=0, limit=0):
        if user.id is None:
            return False
        if (offset > 0) and (limit > 0):
            favorite_records = self.filter(user=user, activate=1).order_by('-updated_at')[offset:offset+limit]
        else:
            favorite_records = self.filter(user=user, activate=1).order_by('-updated_at')
        if favorite_records:
            favorites = []
            for i in favorite_records:
                favorites.append((i.uuid_ue, i.uuid_fp))
            return favorites
        else:
            return False

    def count_favorites(self, user):
        if user.id is None:
            return 0
        record_count = self.filter(user=user, activate=1).count()
        if record_count > 0:
            return record_count
        else:
            return 0

    def check_favorite(self, user, uuid_ue, uuid_fp):
        favorite_records = self.filter(user=user, uuid_ue=uuid_ue, uuid_fp=uuid_fp).order_by('-updated_at')
        if favorite_records:
            activate = favorite_records[0].activate
            if activate:
                return True
            else:
                return False
        else:
            return False


class Favorites(models.Model):
    uuid_ue = models.CharField(max_length=40, default=None, blank=True, null=True)
    uuid_fp = models.CharField(max_length=40, default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activate = models.BooleanField(default=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    objects = models.Manager()
    manager = FavoritesManager()

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['user', 'uuid_ue', 'uuid_fp']),
            models.Index(fields=['user', 'activate']),
            models.Index(fields=['-updated_at']),
            ]

    def __str__(self):
        return f'user: {self.user.email} likes {self.uuid_ue} ,{self.uuid_fp} == {self.activate}'
