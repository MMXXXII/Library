<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()
const members = ref([])
const libraries = ref([])
const memberStats = ref(null)
const searchQuery = ref('')
const formId = ref(null)
const formUsername = ref('')
const formEmail = ref('')
const formAge = ref(null)
const formIsSuperuser = ref(false)
const formLibrary = ref('')
const formPassword = ref('')
const message = ref('')
const showModal = ref(false)

const filteredMembers = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return members.value
  return members.value.filter(m => (m.username || '').toLowerCase().includes(q))
})

async function loadMembers() {
  const res = await axios.get('/members/')
  members.value = res.data
}

async function loadLibraries() {
  const res = await axios.get('/libraries/')
  libraries.value = res.data
}

async function loadStats() {
  const res = await axios.get('/members/stats/')
  memberStats.value = res.data
}

function resetForm() {
  formId.value = null
  formUsername.value = ''
  formEmail.value = ''
  formAge.value = null
  formIsSuperuser.value = false
  formLibrary.value = ''
  formPassword.value = ''
  message.value = ''
}

function openAddModal() {
  resetForm()
  showModal.value = true
}

function openEdit(member) {
  if (!userStore.isSuperUser) return
  formId.value = member.id
  formUsername.value = member.username || ''
  formEmail.value = member.email || ''
  formAge.value = member.age != null ? member.age : null
  formIsSuperuser.value = member.is_superuser || false
  formLibrary.value = member.library || ''
  formPassword.value = ''
  message.value = ''
  showModal.value = true
}

function closeModal() {
  resetForm()
  showModal.value = false
}

async function saveForm() {
  if (!userStore.isSuperUser) {
    message.value = 'Только для администратора'
    return
  }
  if (!formUsername.value || !formEmail.value) {
    message.value = 'Заполните имя и email'
    return
  }
  if (!formId.value && !formPassword.value) {
    message.value = 'При создании читателя укажите пароль для входа'
    return
  }
  message.value = ''
  const payload = {
    username: formUsername.value,
    email: formEmail.value,
    age: formAge.value,
    is_superuser: formIsSuperuser.value
  }
  if (formLibrary.value) payload.library = formLibrary.value
  if (formPassword.value) payload.password = formPassword.value
  if (formId.value) {
    await axios.put('/members/' + formId.value + '/', payload)
  } else {
    await axios.post('/members/', payload)
  }
  closeModal()
  await loadMembers()
  await loadStats()
}

async function deleteMember(member) {
  if (!userStore.isSuperUser) return
  if (!confirm(`Вы точно хотите удалить читателя "${member.username}"?`)) return
  await axios.delete('/members/' + member.id + '/')
  await loadMembers()
  await loadStats()
}

async function exportFile() {
  if (!userStore.isSuperUser) return
  const res = await axios.get('/members/export/', { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = 'Members.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  await userStore.fetchUserInfo()
  await loadLibraries()
  await loadMembers()
  await loadStats()
})
</script>

<template>
  <div class="container mt-4">

    <div class="row mb-3 align-items-center">
      <div class="col">
        <p>Всего читателей: {{ memberStats ? memberStats.count_users : 0 }}</p>
        <p>Админов: {{ memberStats ? memberStats.count_admins : 0 }}</p>
      </div>
      <div class="col-auto d-flex gap-2">
        <button v-if="userStore.isSuperUser" class="btn btn-primary" @click="openAddModal">Добавить читателя</button>
        <button v-if="userStore.isSuperUser" class="btn btn-outline-success" @click="exportFile">Экспорт Excel</button>
      </div>
    </div>

    <div class="row mb-3">
      <div class="col">
        <input class="form-control" placeholder="Поиск по имени" v-model="searchQuery">
      </div>
    </div>

    <ul class="list-group">
      <li v-for="member in filteredMembers" :key="member.id"
        class="list-group-item d-flex justify-content-between align-items-center">
        <div>
          <div>{{ member.username }}</div>
          <div class="text-muted small">
            Email: {{ member.email }} | Возраст: {{ member.age != null ? member.age : '—' }} |
            Роль: {{ member.is_superuser ? 'Администратор' : 'Читатель' }}
          </div>
        </div>
        <div v-if="userStore.isSuperUser" class="d-flex gap-2">
          <button class="btn btn-success btn-sm" @click="openEdit(member)"><i class="bi bi-pen-fill"></i></button>
          <button class="btn btn-danger btn-sm" @click="deleteMember(member)"><i class="bi bi-x"></i></button>
        </div>
      </li>
      <li v-if="filteredMembers.length === 0" class="list-group-item text-center text-muted">Читателей пока нет</li>
    </ul>

    <div v-if="showModal" class="modal d-block" tabindex="-1" style="background: rgba(0,0,0,0.5);">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ formId ? 'Редактировать читателя' : 'Добавить читателя' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body d-flex flex-column gap-2">
            <input class="form-control" placeholder="Имя пользователя" v-model="formUsername">
            <input class="form-control" placeholder="Email" v-model="formEmail">
            <input type="number" class="form-control" placeholder="Возраст" v-model="formAge">
            <input type="password" class="form-control" placeholder="Пароль" v-model="formPassword" autocomplete="new-password">
            <select class="form-select" v-model="formLibrary">
              <option value="">Библиотека</option>
              <option v-for="lib in libraries" :key="lib.id" :value="lib.id">{{ lib.name }}</option>
            </select>
            <select class="form-select" v-model="formIsSuperuser">
              <option :value="false">Читатель</option>
              <option :value="true">Администратор</option>
            </select>
            <div v-if="message" class="alert alert-danger mb-0">{{ message }}</div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="closeModal">Отмена</button>
            <button class="btn btn-primary" @click="saveForm">{{ formId ? 'Сохранить' : 'Добавить' }}</button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>