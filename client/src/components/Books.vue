<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { showNotification, handleApiError } from '../utils'
import { useUserStore } from '../stores/userStore'


const userStore = useUserStore()
const isAdmin = computed(() => userStore.isSuperUser)
const books = ref([])
const genres = ref([])
const libraries = ref([])
const bookStats = ref(null)
const searchQuery = ref('')


const sortBy = ref([{ key: 'title', order: 'asc' }])


const dialogs = reactive({
  add: false, edit: false, delete: false
})
const form = reactive({
  id: null, title: '', genre: '', library: ''
})


const headers = [
  { title: 'Название', key: 'title', sortable: true },
  { title: 'Жанр', key: 'genre_name', sortable: true },
  { title: 'Библиотека', key: 'library_name', sortable: true },
  { title: 'Статус', key: 'status', sortable: true },
  { title: 'Действия', key: 'actions', sortable: false }
]


const filteredBooks = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  
  if (!q) {
    return books.value
  }
  
  return books.value.filter(b => {
    const title = b.title || ''
    return title.toLowerCase().includes(q)
  })
})


async function loadData() {
  const booksRes = await axios.get('/books/')
  const statsRes = await axios.get('/books/stats/')
  const genresRes = await axios.get('/genres/')
  const libsRes = await axios.get('/libraries/')
  
  books.value = booksRes.data.map(b => {
    let genreName = b.genre_name
    if (!genreName && b.genre) {
      genreName = b.genre.name
    }
    if (!genreName) {
      genreName = ''
    }
    
    let libraryName = b.library_name
    if (!libraryName && b.library) {
      libraryName = b.library.name
    }
    if (!libraryName) {
      libraryName = ''
    }
    
    let status = 'Выдана'
    if (b.is_available) {
      status = 'Доступна'
    }
    
    b.genre_name = genreName
    b.library_name = libraryName
    b.status = status
    
    return b
  })
  
  bookStats.value = statsRes.data
  genres.value = genresRes.data
  libraries.value = libsRes.data
}


function resetForm() {
  form.id = null
  form.title = ''
  form.genre = ''
  form.library = ''
}


function openEdit(book) {
  if (!isAdmin.value) {
    return
  }
  form.id = book.id
  form.title = book.title || ''
  form.genre = book.genre?.id || book.genre || ''
  form.library = book.library?.id || book.library || ''
  dialogs.edit = true
}


function openDelete(book) {
  if (!isAdmin.value) {
    return
  }
  form.id = book.id
  form.title = book.title || ''
  dialogs.delete = true
}


async function saveForm() {
  if (!isAdmin.value || !form.title || !form.genre || !form.library) {
    showNotification({ visible: true, message: 'Заполните все поля', type: 'warning' })
    return
  }
  
  if (form.id) {
    await axios.put(`/books/${form.id}/`, { title: form.title, genre: form.genre, library: form.library })
    dialogs.edit = false
    showNotification({ visible: true, message: 'Сохранено', type: 'success' })
  } else {
    await axios.post('/books/', { title: form.title, genre: form.genre, library: form.library })
    dialogs.add = false
    showNotification({ visible: true, message: 'Добавлено', type: 'success' })
  }
  
  resetForm()
  await loadData()
}


async function deleteBook() {
  if (!isAdmin.value) {
    return
  }
  await axios.delete('/books/${form.id}/')
  dialogs.delete = false
  resetForm()
  await loadData()
  showNotification({ visible: true, message: 'Удалено', type: 'danger' })
}


async function exportFile(type) {
  if (!isAdmin.value) {
    return
  }
  const res = await axios.get('/books/export/', {
    params: { type }, responseType: 'blob'
  })
  const url = URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = "Books.${type === 'excel' ? 'xlsx' : 'docx'}"
  a.click()
  URL.revokeObjectURL(url)
}


onMounted(async () => {
  await userStore.fetchUserInfo()
  await loadData()
})
</script>


<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card class="pa-4" elevation="2">
          <div class="d-flex justify-space-between align-center mb-4">
            <div>
              <h2>Книги</h2>
              <div class="text-body-2 text-medium-emphasis">
                Всего: {{ bookStats?.count || 0 }},
                самая популярная: {{ bookStats?.most_borrowed?.title || 'нет данных' }}
              </div>
            </div>
            <div class="d-flex gap-2" v-if="isAdmin">
              <v-btn v-if="isAdmin" color="primary" prepend-icon="mdi-plus" @click="dialogs.add = true">Добавить
                книгу</v-btn>
              <v-btn @click="exportFile('excel')" color="success" variant="outlined"
                prepend-icon="mdi-microsoft-excel">Excel</v-btn>
              <v-btn @click="exportFile('word')" color="indigo" variant="outlined"
                prepend-icon="mdi-file-word">Word</v-btn>
            </div>
          </div>

          <div class="d-flex align-center mb-4 gap-4">
            <v-text-field v-model="searchQuery" label="Поиск по книгам" variant="outlined" clearable
              prepend-inner-icon="mdi-magnify" density="comfortable" class="flex-grow-1" />
          </div>

          <v-data-table :headers="headers" :items="filteredBooks" item-key="id" :items-per-page="10"
            v-model:sort-by="sortBy" class="elevation-1">
            <template #item.status="{ item }">
              <v-chip :color="item.status === 'Доступна' ? 'success' : 'orange'" variant="flat">
                {{ item.status }}
              </v-chip>
            </template>
            <template #item.actions="{ item }">
              <div v-if="isAdmin" class="d-flex gap-1">
                <v-btn variant="text" color="primary" prepend-icon="mdi-pencil" @click="openEdit(item)"
                  size="small"></v-btn>
                <v-btn variant="text" color="error" prepend-icon="mdi-delete" @click="openDelete(item)"
                  size="small"></v-btn>
              </div>
            </template>
            <template #no-data>
              <div class="text-center pa-6">
                <div class="mb-2">Нет книг</div>
                <v-btn v-if="isAdmin" color="primary" prepend-icon="mdi-plus" @click="dialogs.add = true">
                  Добавить книгу
                </v-btn>
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="dialogs.add" max-width="520" v-if="isAdmin">
      <v-card>
        <v-card-title>Добавить книгу</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.title" label="Название" variant="outlined" density="comfortable" class="mb-3" />
          <v-select v-model="form.genre" :items="genres" item-value="id" item-title="name" label="Жанр"
            variant="outlined" density="comfortable" class="mb-3" />
          <v-select v-model="form.library" :items="libraries" item-value="id" item-title="name" label="Библиотека"
            variant="outlined" density="comfortable" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="dialogs.add = false">Отмена</v-btn>
          <v-btn color="primary" @click="saveForm">Добавить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogs.edit" max-width="520" v-if="isAdmin">
      <v-card>
        <v-card-title>Редактировать книгу</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.title" label="Название" variant="outlined" density="comfortable" class="mb-3" />
          <v-select v-model="form.genre" :items="genres" item-value="id" item-title="name" label="Жанр"
            variant="outlined" density="comfortable" class="mb-3" />
          <v-select v-model="form.library" :items="libraries" item-value="id" item-title="name" label="Библиотека"
            variant="outlined" density="comfortable" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="dialogs.edit = false">Отмена</v-btn>
          <v-btn color="primary" @click="saveForm">Сохранить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogs.delete" max-width="420" v-if="isAdmin">
      <v-card>
        <v-card-title>Удалить книгу</v-card-title>
        <v-card-text>Вы уверены, что хотите удалить <strong>{{ form.title }}</strong>?</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="dialogs.delete = false">Отмена</v-btn>
          <v-btn color="error" @click="deleteBook">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>