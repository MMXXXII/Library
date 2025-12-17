<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import QRCode from 'qrcode'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.isSuperUser)

const members = ref([])
const filteredMembers = ref([])
const memberStats = ref(null)

const showAddDialog = ref(false)
const showEditDialog = ref(false)
const showDeleteDialog = ref(false)

const sortBy = ref([{ key: 'username', order: 'asc' }])

const headers = [
  { title: 'Имя', key: 'username', sortable: true },
  { title: 'Email', key: 'email', sortable: true },
  { title: 'Возраст', key: 'age', sortable: true },
  { title: 'Роль', key: 'role', sortable: false },
  { title: 'Действия', key: 'actions', sortable: false }
]

const memberToAdd = reactive({
  username: '',
  email: '',
  password: '',
  age: null,
  is_superuser: false,
  is_staff: false
})

const memberToEdit = reactive({
  id: null,
  username: '',
  email: '',
  password: '',
  age: null,
  is_superuser: false,
  is_staff: false
})

const memberToDelete = reactive({
  id: null,
  username: ''
})

const showTotpDialog = ref(false)
const qrDataUrl = ref('')
const totpUrl = ref('')
const totpCode = ref('')
const totpError = ref(false)
const pendingDeleteId = ref(null)

async function buildQr(u) {
  if (!u) {
    qrDataUrl.value = ''
    return
  }
  qrDataUrl.value = await QRCode.toDataURL(u, { width: 220, margin: 1 })
}

async function loadMembers() {
  const r = await axios.get('/members/')
  members.value = r.data
  filteredMembers.value = members.value.slice()
}

async function loadMemberStats() {
  const r = await axios.get('/members/stats/')
  memberStats.value = r.data
}

async function addMember() {
  if (!isAdmin.value) {
    return
  }
  if (!memberToAdd.username || !memberToAdd.email || !memberToAdd.password) {
    return
  }

  await axios.post('/members/', {
    username: memberToAdd.username,
    email: memberToAdd.email,
    password: memberToAdd.password,
    is_superuser: memberToAdd.is_superuser,
    is_staff: memberToAdd.is_staff,
    age: memberToAdd.age
  })

  memberToAdd.username = ''
  memberToAdd.email = ''
  memberToAdd.password = ''
  memberToAdd.age = null
  memberToAdd.is_superuser = false
  memberToAdd.is_staff = false
  showAddDialog.value = false
  await loadMembers()
  await loadMemberStats()
}

function openEditDialog(member) {
  if (!isAdmin.value) {
    return
  }

  memberToEdit.id = member.id
  memberToEdit.username = member.username || ''
  memberToEdit.email = member.email || ''
  memberToEdit.password = ''
  memberToEdit.age = member.age || null
  memberToEdit.is_superuser = member.is_superuser || false
  memberToEdit.is_staff = member.is_staff || false

  showEditDialog.value = true
}

async function updateMember() {
  if (!isAdmin.value || !memberToEdit.id) {
    return
  }
  await axios.put(`/members/${memberToEdit.id}/`, memberToEdit)

  if (!memberToEdit.is_superuser && userStore.isSuperUser) {
    await userStore.fetchUserInfo()
    return
  }

  showEditDialog.value = false
  await loadMembers()
  await loadMemberStats()
}

function openDeleteDialog(member) {
  if (!isAdmin.value) {
    return
  }
  memberToDelete.id = member.id
  memberToDelete.username = member.username || ''
  showDeleteDialog.value = true
}

async function deleteMember() {
  if (!isAdmin.value || !memberToDelete.id) {
    return
  }

  if (!userStore.isOtpVerified) {
    showDeleteDialog.value = false
    await openTotpDialog(memberToDelete.id)
    return
  }

  await axios.delete(`/members/${memberToDelete.id}/`)
  showDeleteDialog.value = false
  await loadMembers()
  await loadMemberStats()
}

async function exportMembers(type = 'excel') {
  if (!isAdmin.value) {
    return
  }

  const fileType = type === 'excel' ? 'excel' : 'word'
  const fileExtension = fileType === 'excel' ? 'xlsx' : 'docx'
  
  const response = await axios.get(`/members/export/?type=${fileType}`, { 
    responseType: 'blob' 
  })
  
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `members.${fileExtension}`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

async function openTotpDialog(deleteId) {
  pendingDeleteId.value = deleteId
  showTotpDialog.value = true

  totpError.value = false
  totpCode.value = ''
  totpUrl.value = ''
  qrDataUrl.value = ''

  totpUrl.value = await userStore.getTotp()
  if (totpUrl.value) {
    await buildQr(totpUrl.value)
  }
}

function closeTotpDialog() {
  showTotpDialog.value = false
  totpError.value = false
  totpCode.value = ''
  totpUrl.value = ''
  qrDataUrl.value = ''
  pendingDeleteId.value = null
}

async function confirmTotpAndDelete() {
  totpError.value = false

  const ok = await userStore.verifyOtp(totpCode.value)

  if (!ok) {
    totpError.value = true
    totpCode.value = ''
    return
  }

  userStore.isOtpVerified = true

  const id = pendingDeleteId.value
  closeTotpDialog()
  if (id) {
    await axios.delete(`/members/${id}/`)
    await loadMembers()
    await loadMemberStats()
  }
}

onMounted(async () => {
  await userStore.fetchUserInfo()
  await loadMembers()
  await loadMemberStats()
})
</script>

<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card class="pa-4" elevation="2">
          <div class="d-flex justify-space-between align-center mb-4">
            <div>
              <h2 class="mb-1">Читатели</h2>
              <div class="text-body-2 text-medium-emphasis">
                Всего: {{ memberStats?.count_users || 0 }},
                админов: {{ memberStats?.count_admins || 0 }}
              </div>
            </div>
            <div class="d-flex gap-2">
              <v-btn
                v-if="isAdmin"
                color="primary"
                prepend-icon="mdi-plus"
                @click="showAddDialog = true"
                class="mb-4"
              >
                Добавить читателя
              </v-btn>
              <v-btn
                v-if="isAdmin"
                color="success"
                variant="outlined"
                @click="exportMembers('excel')"
                prepend-icon="mdi-microsoft-excel"
              >
                Excel
              </v-btn>
              <v-btn
                v-if="isAdmin"
                color="indigo"
                variant="outlined"
                @click="exportMembers('word')"
                prepend-icon="mdi-file-word"
              >
                Word
              </v-btn>
            </div>
          </div>

          <v-data-table
            :headers="headers"
            :items="filteredMembers"
            item-key="id"
            :items-per-page="10"
            v-model:sort-by="sortBy"
            class="elevation-1"
          >
            <template #item.role="{ item }">
              <v-chip :color="item.is_superuser ? 'error' : 'secondary'" variant="flat" size="small">
                {{ item.is_superuser ? 'Администратор' : 'Читатель' }}
              </v-chip>
            </template>

            <template #item.actions="{ item }">
              <div v-if="isAdmin" class="d-flex gap-1">
                <v-btn
                  variant="text"
                  color="primary"
                  prepend-icon="mdi-pencil"
                  @click="openEditDialog(item)"
                  size="small"
                />
                <v-btn
                  variant="text"
                  color="error"
                  prepend-icon="mdi-delete"
                  @click="openDeleteDialog(item)"
                  size="small"
                />
              </div>
            </template>

            <template #no-data>
              <div class="text-center pa-6">
                <div class="mb-2">Нет читателей</div>
                <div class="text-body-2 mb-3">Добавьте первого читателя, чтобы начать.</div>
                <v-btn
                  v-if="isAdmin"
                  color="primary"
                  prepend-icon="mdi-plus"
                  @click="showAddDialog = true"
                >
                  Добавить читателя
                </v-btn>
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-if="isAdmin" v-model="showAddDialog" max-width="520">
      <v-card>
        <v-card-title>Добавить читателя</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="memberToAdd.username"
            label="Имя пользователя"
            variant="outlined"
            density="comfortable"
            class="mb-3"
            clearable
          />
          <v-text-field
            v-model="memberToAdd.email"
            label="Email"
            variant="outlined"
            density="comfortable"
            class="mb-3"
            clearable
          />
          <v-text-field
            v-model="memberToAdd.password"
            label="Пароль"
            type="password"
            variant="outlined"
            density="comfortable"
            class="mb-3"
            clearable
          />
          <v-text-field
            v-model.number="memberToAdd.age"
            label="Возраст"
            type="number"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />
          <v-switch
            v-model="memberToAdd.is_superuser"
            label="Сделать администратором"
            color="primary"
            inset
          />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="showAddDialog = false">Отмена</v-btn>
          <v-btn color="primary" @click="addMember">Добавить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-if="isAdmin" v-model="showEditDialog" max-width="520">
      <v-card>
        <v-card-title>Редактировать читателя</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="memberToEdit.username"
            label="Имя пользователя"
            variant="outlined"
            density="comfortable"
            class="mb-3"
            clearable
          />
          <v-text-field
            v-model="memberToEdit.email"
            label="Email"
            variant="outlined"
            density="comfortable"
            class="mb-3"
            clearable
          />
          <v-text-field
            v-model="memberToEdit.password"
            label="Новый пароль (оставьте пустым, чтобы не менять)"
            type="password"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />
          <v-text-field
            v-model.number="memberToEdit.age"
            label="Возраст"
            type="number"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />
          <v-switch
            v-model="memberToEdit.is_superuser"
            label="Администратор"
            color="primary"
            inset
          />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="showEditDialog = false">Отмена</v-btn>
          <v-btn color="primary" @click="updateMember">Сохранить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-if="isAdmin" v-model="showDeleteDialog" max-width="420">
      <v-card>
        <v-card-title class="text-h6">Удалить читателя</v-card-title>
        <v-card-text>
          Вы уверены, что хотите удалить читателя
          <strong>{{ memberToDelete.username }}</strong>?
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="showDeleteDialog = false">Отмена</v-btn>
          <v-btn color="error" @click="deleteMember">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-if="isAdmin" v-model="showTotpDialog" max-width="560">
      <v-card>
        <v-card-title>2FA подтверждение</v-card-title>
        <v-card-text>
          <div class="text-medium-emphasis mb-3" style="font-size: 14px;">
            Отсканируйте QR-код и введите код.
          </div>

          <div class="d-flex justify-center mb-3" v-if="qrDataUrl">
            <img :src="qrDataUrl" alt="QR" style="width: 220px; height: 220px;" />
          </div>

          <div v-else class="text-medium-emphasis mb-3" style="font-size: 14px;">
            Не удалось получить QR. Обновите страницу и попробуйте снова.
          </div>

          <v-text-field
            v-model="totpCode"
            label="Код из приложения"
            variant="outlined"
            maxlength="6"
            inputmode="numeric"
          />

          <div v-if="totpError" class="text-error" style="font-size: 14px;">
            Неверный код
          </div>
        </v-card-text>

        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="closeTotpDialog">Отмена</v-btn>
          <v-btn color="error" @click="confirmTotpAndDelete">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>