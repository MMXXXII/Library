<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { showNotification } from '../utils'
import { useUserStore } from '../stores/userStore'


const userStore = useUserStore()
const isAdmin = computed(() => userStore.isSuperUser)
const libraries = ref([])
const filteredLibraries = ref([])
const libraryStats = ref(null)


const searchQuery = ref('')
const sortOrder = ref('asc')


const notification = reactive({ visible: false, message: '', type: 'success' })


const showEditDialog = ref(false)
const showDeleteDialog = ref(false)
const showAddDialog = ref(false)


const libraryToAdd = reactive({ name: '' })
const libraryToEdit = reactive({ id: null, name: '' })
const libraryToDelete = reactive({ id: null, name: '' })


async function loadLibraries() {
  const res = await axios.get('/libraries/')
  libraries.value = res.data
  filterAndSort()
}


async function loadLibraryStats() {
  const res = await axios.get('/libraries/stats/')
  libraryStats.value = res.data
}


function filterAndSort() {
  let list = libraries.value
  const q = searchQuery.value.trim().toLowerCase()

  if (q) {
    list = list.filter(lib => (lib.name || '').toLowerCase().includes(q))
  }

  if (sortOrder.value === 'asc') {
    list = list.slice().sort((a, b) => a.name.localeCompare(b.name))
  } else {
    list = list.slice().sort((a, b) => b.name.localeCompare(a.name))
  }

  filteredLibraries.value = list
}


async function addLibrary() {
  if (!isAdmin.value) {
    return
  }

  const name = libraryToAdd.name.trim()
  if (!name) {
    showNotification({ visible: true, message: 'Введите название библиотеки', type: 'warning' })
    return
  }

  await axios.post('/libraries/', { name })
  libraryToAdd.name = ''
  await loadLibraries()
  await loadLibraryStats()
  showNotification({ visible: true, message: 'Библиотека добавлена', type: 'success' })
  showAddDialog.value = false
}


function openEditDialog(lib) {
  if (!isAdmin.value) {
    return
  }
  libraryToEdit.id = lib.id
  libraryToEdit.name = lib.name || ''
  showEditDialog.value = true
}


async function updateLibrary() {
  if (!isAdmin.value || !libraryToEdit.id) {
    return
  }
  const name = libraryToEdit.name.trim()
  if (!name) {
    showNotification({ visible: true, message: 'Название библиотеки не может быть пустым', type: 'warning' })
    return
  }

  await axios.put(`/libraries/${libraryToEdit.id}/`, { name })
  showEditDialog.value = false
  await loadLibraries()
  await loadLibraryStats()
  showNotification({ visible: true, message: 'Изменения сохранены', type: 'success' })
}


function openDeleteDialog(lib) {
  if (!isAdmin.value) {
    return
  }
  libraryToDelete.id = lib.id
  libraryToDelete.name = lib.name || ''
  showDeleteDialog.value = true
}


async function deleteLibrary() {
  if (!isAdmin.value || !libraryToDelete.id) {
    return
  }

  await axios.delete(`/libraries/${libraryToDelete.id}/`)
  showDeleteDialog.value = false
  await loadLibraries()
  await loadLibraryStats()
  showNotification({ visible: true, message: 'Библиотека удалена', type: 'danger' })
}


async function exportLibraries(type = 'excel') {
  if (!isAdmin.value) {
    return
  }

  const res = await axios.get('/libraries/export/', { params: { type }, responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([res.data]))
  const link = document.createElement('a')
  link.href = url
  link.download = type === 'excel' ? 'libraries.xlsx' : 'libraries.docx'
  document.body.appendChild(link)
  link.click()
  link.remove()
  showNotification({ visible: true, message: 'Файл скачивается', type: 'success' })
}


onMounted(async () => {
  await userStore.fetchUserInfo()
  await loadLibraries()
  await loadLibraryStats()
})
</script>


<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card class="pa-4" elevation="2">
          <div class="d-flex justify-space-between align-center mb-4">
            <div>
              <h2 class="mb-1">Библиотеки</h2>
              <div class="text-body-2 text-medium-emphasis">
                Всего библиотек: {{ libraryStats?.count || 0 }},
                самая популярная: {{ libraryStats?.top || 'нет данных' }}
              </div>
            </div>
            <div class="d-flex gap-2" v-if="isAdmin">
              <v-btn color="primary" prepend-icon="mdi-plus" @click="showAddDialog = true">Добавить библиотеку</v-btn>
              <v-btn color="success" variant="outlined" prepend-icon="mdi-microsoft-excel" @click="exportLibraries('excel')">Excel</v-btn>
              <v-btn color="indigo" variant="outlined" prepend-icon="mdi-file-word" @click="exportLibraries('word')">Word</v-btn>
            </div>
          </div>

          <v-alert v-if="notification.visible" :type="notification.type" class="mb-4" variant="tonal" closable>
            {{ notification.message }}
          </v-alert>

          <v-row class="mb-4" align="center" no-gutters>
            <v-col cols="12" md="6" class="pr-2">
              <v-text-field
                v-model="searchQuery"
                label="Поиск по библиотекам"
                variant="outlined"
                density="comfortable"
                clearable
                prepend-inner-icon="mdi-magnify"
                @input="filterAndSort"
              />
            </v-col>
            <v-col cols="12" md="6" class="pl-2">
              <v-select
                v-model="sortOrder"
                :items="[ { title: 'От A до Я', value: 'asc' }, { title: 'От Я до A', value: 'desc' } ]"
                item-title="title"
                item-value="value"
                label="Сортировка"
                variant="outlined"
                density="comfortable"
                @update:model-value="filterAndSort"
              />
            </v-col>
          </v-row>

          <v-list lines="one">
            <v-list-item v-for="lib in filteredLibraries" :key="lib.id" :title="lib.name">
              <template #append>
                <div v-if="isAdmin" class="d-flex gap-2">
                  <v-btn icon size="small" variant="text" color="primary" @click.stop="openEditDialog(lib)">
                    <v-icon icon="mdi-pencil" />
                  </v-btn>
                  <v-btn icon size="small" variant="text" color="error" @click.stop="openDeleteDialog(lib)">
                    <v-icon icon="mdi-delete" />
                  </v-btn>
                </div>
              </template>
            </v-list-item>
            <v-list-item v-if="!filteredLibraries.length" title="Библиотек пока нет" subtitle="Добавьте первую библиотеку." />
          </v-list>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="showAddDialog" max-width="420" v-if="isAdmin">
      <v-card>
        <v-card-title>Добавить библиотеку</v-card-title>
        <v-card-text>
          <v-text-field v-model="libraryToAdd.name" label="Название библиотеки" variant="outlined" density="comfortable" />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="showAddDialog = false">Отмена</v-btn>
          <v-btn color="primary" @click="addLibrary">Добавить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showEditDialog" max-width="420" v-if="isAdmin">
      <v-card>
        <v-card-title>Редактировать библиотеку</v-card-title>
        <v-card-text>
          <v-text-field v-model="libraryToEdit.name" label="Название библиотеки" variant="outlined" density="comfortable" />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="showEditDialog = false">Отмена</v-btn>
          <v-btn color="primary" @click="updateLibrary">Сохранить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showDeleteDialog" max-width="420" v-if="isAdmin">
      <v-card>
        <v-card-title class="text-h6">Удалить библиотеку</v-card-title>
        <v-card-text>Вы уверены, что хотите удалить библиотеку <strong>{{ libraryToDelete.name }}</strong>?</v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="showDeleteDialog = false">Отмена</v-btn>
          <v-btn color="error" @click="deleteLibrary">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>
