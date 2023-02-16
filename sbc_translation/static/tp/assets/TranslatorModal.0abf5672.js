var r=Object.defineProperty;var n=(e,s,t)=>s in e?r(e,s,{enumerable:!0,configurable:!0,writable:!0,value:t}):e[s]=t;var a=(e,s,t)=>(n(e,typeof s!="symbol"?s+"":s,t),t);import{C as d,x as c,M as x,L as m,_ as o,u as f,o as p,m as v,n as h}from"./index.79c05fa8.js";import{T as b}from"./TranslationSkills.c9d4f6f3.js";class l extends d{constructor(){super(...arguments);a(this,"_",o);a(this,"state",f({loading:!1,active:!1,translator:void 0,title:void 0}))}setup(){this.fetchTranslator(this.props.translatorId),p(t=>{this.fetchTranslator(t.translatorId)})}onClose(){this.props.onClose(),setTimeout(()=>{this.state.translator=void 0,this.state.title=void 0},300)}fetchTranslator(t){t?(this.state.loading=!0,this.state.active=!0,v.translators.find(t).then(i=>{i?(this.state.loading=!1,this.state.translator=i,this.state.title=i.name):(h.error(o("User not found")),this.state.active=!1,this.state.loading=!1,this.props.onClose())})):(this.state.active=!1,this.state.loading=!1)}}a(l,"template",c`
    <Modal title="state.title" active="state.active" onClose="() => this.onClose()" loading="state.loading">
      <div t-if="state.translator" class="w-156 grid grid-cols-2">
        <div class="bg-slate-100 border-r border-solid border-slate-200 p-4">
          <div class="mb-4">
            <div class="flex mb-2">
              <p class="font-semibold text-sm text-slate-700 w-32">Identifier</p>
              <p class="text-sm text-slate-700" t-esc="props.translatorId" />
            </div>
            <div class="flex mb-2">
              <p class="font-semibold text-sm text-slate-700 w-32">Name</p>
              <p class="text-sm text-slate-700" t-esc="state.translator.name" />
            </div>
            <div class="flex mb-2">
              <p class="font-semibold text-sm text-slate-700 w-32">E-Mail</p>
              <p class="text-sm text-slate-700" t-esc="state.translator.email" />
            </div>
            <div class="flex mb-2">
              <p class="font-semibold text-sm text-slate-700 w-32">Language</p>
              <p class="text-sm text-slate-700" t-esc="_(state.translator.language)" />
            </div>
          </div>
          <div class="flex justify-around">
            <div class="flex flex-col items-center">
              <h3 class="font-semibold text-xl text-slate-800" t-esc="state.translator.year" />
              <p class="font-medium text-xs text-slate-600">This Year</p>
            </div>
            <div class="flex flex-col items-center">
              <h3 class="font-semibold text-xl text-slate-800" t-esc="state.translator.lastYear" />
              <p class="font-medium text-xs text-slate-600">Last Year</p>
            </div>
            <div class="flex flex-col items-center">
              <h3 class="font-semibold text-xl text-slate-800" t-esc="state.translator.total" />
              <p class="font-medium text-xs text-slate-600">All Time</p>
            </div>
          </div>
        </div>
        <div class="p-4 flex flex-col items-center">
          <h3 class="font-semibold text-sm text-slate-700 mb-2">Translation Skills</h3>
          <TranslationSkills skills="state.translator.skills" />
        </div>
      </div>
    </Modal>
  `),a(l,"props",{translatorId:{type:Number,optional:!0},onClose:{type:Function,optional:!0}}),a(l,"components",{Modal:x,Loader:m,TranslationSkills:b});var C=l;export{C as T};
