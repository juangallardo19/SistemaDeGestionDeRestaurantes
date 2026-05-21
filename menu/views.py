from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.decorators import admin_required, mesero_required
from orders.carrito import Carrito

from .forms import CategoriaForm, IngredienteForm, PlatoForm
from .models import Categoria, Ingrediente, Plato


# ── Categorías ────────────────────────────────────────────────────────────────

@login_required
def lista_categorias(request):
    categorias = Categoria.objects.all()
    return render(request, 'menu/lista_categorias.html', {'categorias': categorias})


@admin_required
def crear_categoria(request):
    form = CategoriaForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Categoría creada exitosamente.')
        return redirect('menu:lista_categorias')
    return render(request, 'menu/form_categoria.html', {'form': form, 'titulo': 'Crear Categoría'})


@admin_required
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    form = CategoriaForm(request.POST or None, request.FILES or None, instance=categoria)
    if form.is_valid():
        form.save()
        messages.success(request, 'Categoría actualizada exitosamente.')
        return redirect('menu:lista_categorias')
    return render(request, 'menu/form_categoria.html', {
        'form': form,
        'titulo': 'Editar Categoría',
        'objeto': categoria,
    })


@admin_required
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria.activo = False
        categoria.save()
        messages.success(request, 'Categoría desactivada.')
        return redirect('menu:lista_categorias')
    return render(request, 'menu/confirmar_eliminar.html', {
        'objeto': categoria,
        'tipo': 'categoría',
        'cancelar_url': reverse('menu:lista_categorias'),
    })


# ── Platos ────────────────────────────────────────────────────────────────────

@login_required
def lista_platos(request):
    categorias = Categoria.objects.filter(activo=True)
    try:
        categoria_id = int(request.GET.get('categoria', ''))
    except (ValueError, TypeError):
        categoria_id = None

    platos = Plato.objects.filter(disponible=True).select_related('categoria')
    if categoria_id:
        platos = platos.filter(categoria_id=categoria_id)

    return render(request, 'menu/lista_platos.html', {
        'platos': platos,
        'categorias': categorias,
        'categoria_id': categoria_id,
        'query': '',
        'carrito': Carrito(request),
    })


@login_required
def detalle_plato(request, pk):
    plato = get_object_or_404(Plato, pk=pk)
    return render(request, 'menu/detalle_plato.html', {'plato': plato})


@admin_required
def crear_plato(request):
    form = PlatoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Plato creado exitosamente.')
        return redirect('menu:list')
    return render(request, 'menu/form_plato.html', {'form': form, 'titulo': 'Crear Plato'})


@admin_required
def editar_plato(request, pk):
    plato = get_object_or_404(Plato, pk=pk)
    form = PlatoForm(request.POST or None, request.FILES or None, instance=plato)
    if form.is_valid():
        form.save()
        messages.success(request, 'Plato actualizado exitosamente.')
        return redirect('menu:list')
    return render(request, 'menu/form_plato.html', {
        'form': form,
        'titulo': 'Editar Plato',
        'objeto': plato,
    })


@admin_required
def eliminar_plato(request, pk):
    plato = get_object_or_404(Plato, pk=pk)
    if request.method == 'POST':
        plato.disponible = False
        plato.save()
        messages.success(request, 'Plato desactivado.')
        return redirect('menu:list')
    return render(request, 'menu/confirmar_eliminar.html', {
        'objeto': plato,
        'tipo': 'plato',
        'cancelar_url': reverse('menu:list'),
    })


# ── Ingredientes ──────────────────────────────────────────────────────────────

@login_required
def lista_ingredientes(request):
    ingredientes = Ingrediente.objects.all()
    return render(request, 'menu/lista_ingredientes.html', {'ingredientes': ingredientes})


@admin_required
def crear_ingrediente(request):
    form = IngredienteForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Ingrediente creado exitosamente.')
        return redirect('menu:lista_ingredientes')
    return render(request, 'menu/form_ingrediente.html', {'form': form, 'titulo': 'Crear Ingrediente'})


@admin_required
def editar_ingrediente(request, pk):
    ingrediente = get_object_or_404(Ingrediente, pk=pk)
    form = IngredienteForm(request.POST or None, instance=ingrediente)
    if form.is_valid():
        form.save()
        messages.success(request, 'Ingrediente actualizado exitosamente.')
        return redirect('menu:lista_ingredientes')
    return render(request, 'menu/form_ingrediente.html', {
        'form': form,
        'titulo': 'Editar Ingrediente',
        'objeto': ingrediente,
    })


@admin_required
def eliminar_ingrediente(request, pk):
    ingrediente = get_object_or_404(Ingrediente, pk=pk)
    if request.method == 'POST':
        ingrediente.activo = False
        ingrediente.save()
        messages.success(request, 'Ingrediente desactivado.')
        return redirect('menu:lista_ingredientes')
    return render(request, 'menu/confirmar_eliminar.html', {
        'objeto': ingrediente,
        'tipo': 'ingrediente',
        'cancelar_url': reverse('menu:lista_ingredientes'),
    })


# ── Búsqueda ──────────────────────────────────────────────────────────────────

@login_required
def buscar_platos(request):
    query = request.GET.get('q', '').strip()
    try:
        categoria_id = int(request.GET.get('categoria', ''))
    except (ValueError, TypeError):
        categoria_id = None

    categorias = Categoria.objects.filter(activo=True)
    platos = Plato.objects.filter(disponible=True).select_related('categoria')

    if query:
        platos = platos.filter(nombre__icontains=query)
    if categoria_id:
        platos = platos.filter(categoria_id=categoria_id)

    return render(request, 'menu/lista_platos.html', {
        'platos': platos,
        'categorias': categorias,
        'categoria_id': categoria_id,
        'query': query,
        'carrito': Carrito(request),
    })
