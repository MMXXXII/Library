<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/userStore'

const router = useRouter()
const userStore = useUserStore()

async function handleLogout() {
  await userStore.logout()
  router.push('/login')
}

onMounted(() => {
  userStore.fetchUserInfo()
})
</script>

<template>
  <div class="container mt-3 mb-3 d-flex align-items-center gap-2 flex-wrap">

    <button v-if="userStore.isAuthenticated" type="button" class="btn btn-light" @click="$router.push('/genres')">Жанры</button>
    <button v-if="userStore.isAuthenticated" type="button" class="btn btn-light" @click="$router.push('/libraries')">Библиотеки</button>
    <button v-if="userStore.isAuthenticated" type="button" class="btn btn-light" @click="$router.push('/books')">Книги</button>
    <button v-if="userStore.isAuthenticated && userStore.isSuperUser" type="button" class="btn btn-light" @click="$router.push('/members')">Читатели</button>
    <button v-if="userStore.isAuthenticated" type="button" class="btn btn-light" @click="$router.push('/loans')">Выдачи</button>

    <div class="ms-auto d-flex gap-2 align-items-center">
      <div class="dropdown" v-if="userStore.isAuthenticated">
        <button class="btn btn-secondary dropdown-toggle" type="button" id="profileDropdown" data-bs-toggle="dropdown" aria-expanded="false">
          {{ userStore.user && userStore.user.username ? userStore.user.username : 'Профиль' }}
        </button>
        <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="profileDropdown">
          <li><a class="dropdown-item" @click="$router.push('/profile')">Мой профиль</a></li>
          <li><hr class="dropdown-divider"></li>
          <li><a class="dropdown-item text-danger" @click="handleLogout">Выход</a></li>
        </ul>
      </div>

      <button v-if="userStore.isAuthenticated" type="button" class="btn btn-light" @click="window.open('/admin', '_blank')">Админка</button>
    </div>
  </div>

  <router-view />
</template>
