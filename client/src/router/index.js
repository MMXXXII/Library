import { createRouter, createWebHistory } from "vue-router"
import { useUserStore } from '../stores/userStore'
import Genres from "../components/Genres.vue"
import Libraries from "../components/Libraries.vue"
import Books from "../components/Books.vue"
import Members from "../components/Members.vue"
import Loans from "../components/Loans.vue"
import Profile from "../components/Profile.vue"
import Login from "../components/Login.vue"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { 
      path: "/", 
      redirect: "/books" 
    },
    { 
      path: "/genres", 
      component: Genres
    },
    { 
      path: "/libraries", 
      component: Libraries
    },
    { 
      path: "/books", 
      component: Books
    },
    { 
      path: "/members", 
      component: Members
    },
    { 
      path: "/loans", 
      component: Loans
    },
    { 
      path: "/profile", 
      component: Profile
    },
    { 
      path: "/login", 
      name: "Login",
      component: Login 
    },
    { 
      path: '/:pathMatch(.*)*', 
      redirect: '/books'
    }
  ]
})

router.beforeEach(async (to) => {
  const userStore = useUserStore()

  if (!userStore.isAuthenticated) {
    await userStore.fetchUserInfo()
  }

  if (to.path !== '/login' && !userStore.isAuthenticated) {
    return { name: 'Login' }
  }

  if (to.path === '/login' && userStore.isAuthenticated) {
    return '/books'
  }

  return true
})


export default router
