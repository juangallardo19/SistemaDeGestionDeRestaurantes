from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomUser

ROLE_GROUP_MAP = {
    'cliente': 'Clientes',
    'mesero': 'Meseros',
    'admin': 'Administradores',
}


@receiver(post_save, sender=CustomUser)
def asignar_grupo_por_rol(sender, instance, created, **kwargs):
    if created:
        group_name = ROLE_GROUP_MAP.get(instance.role)
        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            instance.groups.add(group)
