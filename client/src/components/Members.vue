<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.isSuperUser)

const members = ref([])
const memberStats = ref(null)
const searchQuery = ref('')

const dialogAdd = ref(false)
const dialogEdit = ref(false)
const dialogDelete = ref(false)
const dialogDelete2FA = ref(false)
const formId = ref(null)
const formUsername = ref('')
const formEmail = ref('')
const formAge = ref(null)
const formIsSuperuser = ref(false)

const filteredMembers = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return members.value
  return members.value.filter(m => (m.username || '').toLowerCase().includes(q))
})

async function loadMembers() {
  members.value = (await axios.get('/members/')).data
}

async function loadMemberStats() {
  memberStats.value = (await axios.get('/members/stats/')).data
}

function resetForm() {
  formId.value = null
  formUsername.value = ''
  formEmail.value = ''
  formAge.value = null
  formIsSuperuser.value = false
}

function openAdd() {
  resetForm()
  dialogAdd.value = true
}

function openEdit(member) {
  if (!isAdmin.value) return
  formId.value = member.id
  formUsername.value = member.username || ''
  formEmail.value = member.email || ''
  formAge.value = member.age || null
  formIsSuperuser.value = member.is_superuser || false
  dialogEdit.value = true
}

function openDelete(member) {
  if (!isAdmin.value) return
  formId.value = member.id
  formUsername.value = member.username || ''
  dialogDelete.value = true
}

function openDelete2FA(member) {
  if (!isAdmin.value) return
  formId.value = member.id
  formUsername.value = member.username || ''
  dialogDelete2FA.value = true
}

async function delete2FA() {
  if (!isAdmin.value) return
  await axios.delete(`/members/${formId.value}/2fa/`)
  dialogDelete2FA.value = false
  resetForm()
  await loadMembers()
}

async function saveForm() {
  if (!isAdmin.value || !formUsername.value || !formEmail.value) return

  const payload = {
    username: formUsername.value,
    email: formEmail.value,
    age: formAge.value,
    is_superuser: formIsSuperuser.value
  }

  if (formId.value) {
    await axios.put(`/members/${formId.value}/`, payload)
    dialogEdit.value = false
  } else {
    await axios.post('/members/', payload)
    dialogAdd.value = false
  }

  resetForm()
  await loadMembers()
  await loadMemberStats()
}

async function deleteMember() {
  if (!isAdmin.value) return
  await axios.delete(`/members/${formId.value}/`)
  dialogDelete.value = false
  resetForm()
  await loadMembers()
  await loadMemberStats()
}

async function exportFile() {
  if (!isAdmin.value) return
  const res = await axios.get('/members/export/?type=excel', { responseType: 'blob' })
  const url = URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = 'Members.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  await userStore.fetchUserInfo()
  await loadMembers()
  await loadMemberStats()
})
</script>

<template>
  <div class="container mt-4">
    <div class="row mb-3">
      <div class="col">
        <p>Всего читателей: {{ memberStats?.count_users || 0 }}</p>
        <p>Админов: {{ memberStats?.count_admins || 0 }}</p>
      </div>
      <div class="col-auto" v-if="isAdmin">
        <button class="btn btn-primary me-2" @click="openAdd">Добавить читателя</button>
        <button class="btn btn-outline-success" @click="exportFile">Экспорт Excel</button>
      </div>
    </div>

    <div class="row mb-3">
      <div class="col">
        <input type="text" class="form-control" placeholder="Поиск по имени" v-model="searchQuery">
      </div>
    </div>

    <ul class="list-group">
      <li v-for="member in filteredMembers" :key="member.id" class="list-group-item d-flex justify-content-between align-items-center">
        <div>
          <div>{{ member.username }}</div>
          <div class="text-muted small">
            Email: {{ member.email }} | Возраст: {{ member.age || '—' }} | Роль: {{ member.is_superuser ? 'Администратор' : 'Читатель' }} | 2FA: {{ member.has_2fa ? 'Включен' : 'Выключен' }}
          </div>
        </div>
        <div class="d-flex gap-2" v-if="isAdmin">
          <button class="btn btn-success btn-sm" @click="openEdit(member)">
            <i class="bi bi-pen-fill"></i>
          </button>
          <button class="btn btn-danger btn-sm" @click="openDelete(member)">
            <i class="bi bi-x"></i>
          </button>
          <button v-if="member.has_2fa" class="btn btn-danger btn-sm" @click="openDelete2FA(member)">
            <i class="bi bi-shield-lock-fill"></i>
          </button>
        </div>
      </li>
      <li v-if="!filteredMembers.length" class="list-group-item text-center text-muted">
        Читателей пока нет
      </li>
    </ul>

    <div class="mt-3"></div>

    <div class="modal fade" tabindex="-1" :class="{ show: dialogDelete2FA }" style="display: block;" v-if="dialogDelete2FA && isAdmin">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Удалить 2FA</h5>
            <button type="button" class="btn-close" @click="dialogDelete2FA = false"></button>
          </div>
          <div class="modal-body">
            <p>Вы уверены, что хотите удалить двухфакторную аутентификацию у {{ formUsername }}?</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="dialogDelete2FA = false">Отмена</button>
            <button class="btn btn-danger" @click="delete2FA">Удалить 2FA</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
