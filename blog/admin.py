from django.contrib import admin

from .models import Post, Comment


# 1st variant
# admin.site.register(Post)

# 2nd variant
# Декоратор @admin.register() выполняет те же действия, что и функция admin.site.register():
# регистрирует декорируемый класс наследник ModelAdmin.
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # Атрибут list_display позволяет перечислить поля модели, которые мы хотим отображать на странице списка
    list_display = ('title', 'slug', 'author', 'publish', 'status')
    # Справа на странице появился блок фильтрации списка, который фильтрует статьи по полям, перечисленным в list_filter
    list_filter = ('status', 'created', 'publish', 'author')
    # Строка поиска добавляется для моделей, для которых определен атрибут search_fields
    search_fields = ('title', 'body')
    # Поле slug генерируется автоматически из поля title с помощью атрибута prepopulated_fields (ПРИ ДОБАВЛЕНИИ ПОСТА)
    prepopulated_fields = {'slug': ('title',)}
    # Поле author содержит поле поиска, это упрощает выбор автора из выпадающего списка, когда в системе сотни пользователей (ПРИ ДОБАВЛЕНИИ ПОСТА)
    raw_id_fields = ('author',)
    # Под поиском благодаря атрибуту date_hierarchy добавлены ссылки для навигации по датам.
    date_hierarchy = 'publish'
    # По умолчанию статьи­ отсортированы по полям status и publish
    ordering = ('status', 'publish')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'post', 'created', 'active')
    list_filter = ('active', 'created', 'updated')
    search_fields = ('name', 'email', 'body')
