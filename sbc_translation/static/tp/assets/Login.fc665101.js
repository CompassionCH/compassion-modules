var i=Object.defineProperty;var n=(e,t,s)=>t in e?i(e,t,{enumerable:!0,configurable:!0,writable:!0,value:s}):e[t]=s;var a=(e,t,s)=>(n(e,typeof t!="symbol"?t+"":t,s),s);import{C as r,x as c,b as d,p as m,u as p,B as u,L as h,d as x,q as f,O as g,n as w,_ as b,s as v}from"./index.79c05fa8.js";class o extends r{constructor(){super(...arguments);a(this,"user",d());a(this,"webPath",m);a(this,"state",p({username:"",password:"",loading:!1,settingsModal:!1}))}async login(){this.state.loading=!0;const{username:s,password:l}=this.state;await g.authenticate(s,l)?(await this.user.refresh(),v.username=s,location.reload()):(w.error(b("Failed to log in, incorrect credentials")),this.state.loading=!1)}}a(o,"template",c`
    <SettingsModal active="state.settingsModal" onClose="() => state.settingsModal = false" />
    <div class="w-full h-screen bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
      <div class="flex shadow-xl relative rounded-sm overflow-hidden">
        <div class="h-full bg-white py-20 w-80 px-10">
          <img t-att-src="webPath('/logo_simple.png')" class="block mx-auto w-16 mb-3" />
          <h3 class="text-center text-slate-600 h-6">Compassion</h3>
          <h1 class="text-center text-slate-800 font-light text-2xl mb-5">Translation Platform</h1>
          <form t-on-submit.prevent="login">
            <input class="compassion-input text-sm mb-3" type="text" placeholder="Username" t-model="state.username" />
            <input class="compassion-input text-sm mb-3" type="password" placeholder="Password" t-model="state.password" />
            <Button color="'compassion'" class="'w-full mb-2'" size="'sm'">Login</Button>
            <div class="flex justify-between">
              <a href="#" class="text-xs text-slate-500 hover:text-slate-800 transition-colors">Forgot my password</a>
              <a href="#" class="text-xs text-slate-500 hover:text-slate-800 transition-colors" t-on-click="() => state.settingsModal = true">Language</a>
            </div>
          </form>
        </div>
        <img t-att-src="webPath('/splash.jpg')" class="object-cover w-128 shadow-inner" />
        <Transition active="state.loading" t-slot-scope="scope">
          <div class="absolute top-0 left-0 bg-white-20 w-full h-full flex items-center justify-center" t-att-class="scope.itemClass">
            <div class="bg-white p-10 shadow-2xl rounded-sm">
              <Loader class="'text-3xl'" />
            </div>
          </div>
        </Transition>
      </div>
    </div>
  `),a(o,"components",{Button:u,Loader:h,Transition:x,SettingsModal:f});export{o as default};
