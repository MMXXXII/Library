<script setup>
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
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

function getFilteredMembers() {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return members.value
  return members.value.filter(m => {
    const name = m.username || ''
    return name.toLowerCase().includes(q)
  })
}

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

function openEdit(member) {
  if (!isSuperUser.value) return
  formId.value = member.id
  formUsername.value = member.username || ''
  formEmail.value = member.email || ''
  formAge.value = member.age != null ? member.age : null
  formIsSuperuser.value = member.is_superuser || false
  formLibrary.value = member.library || ''
  formPassword.value = ''
  message.value = ''
}

async function saveForm() {
  if (!isSuperUser.value) {
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
  resetForm()
  await loadMembers()
  await loadStats()
}

async function deleteMember(member) {
  if (!isSuperUser.value) {
    message.value = 'Только для администратора'
    return
  }
  message.value = ''
  await axios.delete('/members/' + member.id + '/')
  await loadMembers()
  await loadStats()
}

async function exportFile() {
  if (!isSuperUser.value) return
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

    <div class="row mb-3">
      <div class="col">
        <p>Всего читателей: {{ memberStats ? memberStats.count_users : 0 }}</p>
        <p>Админов: {{ memberStats ? memberStats.count_admins : 0 }}</p>
      </div>
      <div class="col-auto" v-if="isSuperUser">
        <button class="btn btn-outline-success" @click="exportFile">Экспорт Excel</button>
      </div>
    </div>

    <div v-if="isSuperUser" class="row g-2 mb-3">
      <div class="col">
        <input class="form-control" placeholder="Имя пользователя" v-model="formUsername">
      </div>
      <div class="col">
        <input class="form-control" placeholder="Email" v-model="formEmail">
      </div>
      <div class="col">
        <input type="number" class="form-control" placeholder="Возраст" v-model="formAge">
      </div>
      <div class="col">
        <input type="password" class="form-control" placeholder="Пароль" v-model="formPassword" autocomplete="new-password">
      </div>
      <div class="col">
        <select class="form-select" v-model="formLibrary">
          <option value="">Библиотека</option>
          <option v-for="lib in libraries" :key="lib.id" :value="lib.id">{{ lib.name }}</option>
        </select>
      </div>
      <div class="col">
        <select class="form-select" v-model="formIsSuperuser">
          <option :value="false">Читатель</option>
          <option :value="true">Администратор</option>
        </select>
      </div>
      <div class="col-auto">
        <button class="btn btn-primary" @click="saveForm">{{ formId ? 'Сохранить' : 'Добавить' }}</button>
      </div>
    </div>
    <div v-if="message" class="alert alert-danger">{{ message }}</div>

    <div class="row mb-3">
      <div class="col">
        <input class="form-control" placeholder="Поиск по имени" v-model="searchQuery">
      </div>
    </div>

    <ul class="list-group">
      <li v-for="member in getFilteredMembers()" :key="member.id" class="list-group-item d-flex justify-content-between align-items-center">
        <div>
          <div>{{ member.username }}</div>
          <div class="text-muted small">
            Email: {{ member.email }} | Возраст: {{ member.age != null ? member.age : '—' }} |
            Роль: {{ member.is_superuser ? 'Администратор' : 'Читатель' }}
          </div>
        </div>
        <div v-if="isSuperUser" class="d-flex gap-2">
          <button class="btn btn-success btn-sm" @click="openEdit(member)"><i class="bi bi-pen-fill"></i></button>
          <button class="btn btn-danger btn-sm" @click="deleteMember(member)"><i class="bi bi-x"></i></button>
        </div>
      </li>
      <li v-if="getFilteredMembers().length === 0" class="list-group-item text-center text-muted">Читателей пока нет</li>
    </ul>

  </div>
</template>