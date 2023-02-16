var v=Object.defineProperty;var x=(a,l,t)=>l in a?v(a,l,{enumerable:!0,configurable:!0,writable:!0,value:t}):a[l]=t;var e=(a,l,t)=>(x(a,typeof l!="symbol"?l+"":l,t),t);import{x as p,C as u,T as y,I as w,B as g,R as b,_ as i,u as m,m as r,M as S,n as h,a as T,b as C,c as L}from"./index.79c05fa8.js";import{T as B}from"./TranslationSkills.c9d4f6f3.js";import{b as I,s as M,a as _}from"./tutorial.228562da.js";var R=p`<div class="relative">
  <BlurLoader active="state.loading or currentTranslator.loading" fixed="true" class="'ml-10'" />
  <div class="container mx-auto" t-if="!state.loading and !currentTranslator.loading">
    <LanguagesPickModal active="state.manageSkillsModal" onClose="() => this.closeSkillsModal()" translatorId="currentTranslator.data.translatorId" onChange="() => this.onSkillsChange()" />
    <div class="pt-20">
      <h3 class="text-slate-600 font-light text-2xl text-center">Compassion</h3>
      <h1 class="text-slate-700 font-light text-5xl text-center">Translation Platform</h1>
    </div>
    <t t-if="state.skillLetters.length gt 0">
      <p class="text-slate-700 text-center mt-10 mb-5">
        Welcome <t t-esc="currentTranslator.data.name" />. Here is the list of texts waiting to be translated, <br/>
        please pick one according to your translation skills. You can also register new ones.
      </p>
      <div class="flex justify-center mb-10">
        <Button size="'sm'" level="'secondary'" onClick="() => this.state.manageSkillsModal = true">Add new translation skills</Button>
      </div>
      <div class="flex flex-wrap mt-5 gap-10 justify-center waiting-letters-cards">
        <TranslationCard t-if="state.savedLetters and state.savedLetters.total gt 0" title="_('Saved Letters')"
          remaining="state.savedLetters.total"
          letters="state.savedLetters.data"
          status="'highlight'" />
        <TranslationCard t-foreach="state.skillLetters"
          t-as="item" t-key="item_index"
          title="_(item.skill.source) + ' -> ' + _(item.skill.target)"
          status="item.skill.verified ? undefined : 'unverified'"
          remaining="item.total"
          letters="item.letters" />
      </div>
      <div class="py-10">
        <h3 class="text-slate-600 font-light text-2xl text-center">Thank you.</h3>
      </div>
    </t>
    <div t-else="">
      <p class="text-slate-700 text-center my-10">
        Welcome <t t-esc="currentTranslator.name" />. It seems that you don't have any skill currently defined. Start by picking the languages you are confident in.
      </p>
      <div class="flex justify-center">
        <Button color="'compassion'" onClick="() => this.state.manageSkillsModal = true">Pick Languages</Button>
      </div>
    </div>
  </div>
</div>`;class n extends u{}e(n,"template",p`
    <Tippy content="props.content">
      <Icon icon="'circle-question'" class="props.class || 'text-slate-400'" />
    </Tippy>
  `),e(n,"props",{class:{type:String,optional:!0},content:{type:String}}),e(n,"components",{Tippy:y,Icon:w});class c extends u{constructor(){super(...arguments);e(this,"_",i)}}e(c,"template",p`
    <div class="bg-white rounded-sm ring-2 w-72 overflow-hidden flex flex-col" t-att-class="{
      'ring-compassion ring-opacity-70': props.status === 'highlight',
      'ring-yellow-300 ring-opacity-80': props.status === 'unverified',
      'ring-slate-200 ring-opacity-30': props.status === undefined,
    }">
      <div class="bg-slate-100 px-4 py-3 flex justify-between">
        <div>
          <h4 class="font-light text-lg text-slate-700" t-esc="props.title" />
          <p t-if="props.status !== 'unverified'" class="text-slate-600 text-xs"><t t-esc="props.remaining" /> Texts remaining</p>
          <p t-else="" class="text-slate-600 text-xs">Waiting for validation</p>
        </div>
        <div>
          <Helper t-if="props.status === 'highlight'" content="_('These letters are your saved work in progress waiting to be submitted')" />
          <Helper t-if="props.status === 'unverified'" content="_('This translation skill is currently waiting to be validated, please translate the given letter for it to be reviewed')" />
        </div>
      </div>
      <div class="p-4 bg-white flex-1">
        <div t-if="props.letters.length === 0">
          <p class="text-slate-400 text-center">There's currently no letters to translate here</p>
        </div>
        <t t-else="">
          <div t-if="props.status !== 'unverified'">
            <RouterLink to="'/letters/letter-edit/' + props.letters[0].id">
              <Button icon="'star'" color="'compassion'" level="props.status === 'highlight' ? 'primary' : 'secondary'" class="'w-full mb-2'" size="'sm'">Take the first</Button>
            </RouterLink>
            <RouterLink t-foreach="props.letters" t-as="text" t-key="text.id" to="'/letters/letter-edit/' + text.id">
              <button class="block text-sm text-slate-700 hover:text-compassion hover:translate-x-0.5 transform transition-all mb-1">
                <span class="font-semibold" t-esc="text.child.ref" />
                <span class="pl-2" t-out="'(' + text.date.toLocaleDateString() + ')'" />
              </button>
            </RouterLink>
          </div>
          <div t-else="">
            <RouterLink t-if="props.letters.length gt 0" to="'/letters/letter-edit/' + props.letters[0].id">
              <Button icon="'star'" color="'compassion'" level="props.highlight ? 'primary' : 'secondary'" class="'w-full mb-2'" size="'sm'">Translate Verification Letter</Button>
            </RouterLink>
            <p class="text-center text-slate-600 text-sm">This skill must be validated, to do so you must first translate a letter which will be double checked at Compassion</p>
          </div>
        </t>
      </div>
    </div>
  `),e(c,"props",{title:{type:String},remaining:{type:Number},letters:{type:Array},status:{type:String,optional:!0}}),e(c,"components",{Button:g,RouterLink:b,Helper:n});var P=c,Y=()=>{const a=m({data:[],loading:!1});return a.loading=!0,r.settings.languages().then(l=>{a.data=l,a.loading=!1}),a};class d extends u{constructor(){super(...arguments);e(this,"_",i);e(this,"languages",Y());e(this,"state",m({competences:[],potentialSkills:[],allowedCompetences:[],translator:void 0,loading:!1}))}translatorHasSkill(t){var s;return((s=this.state.translator)==null?void 0:s.skills.find(o=>o.source===t.source&&o.target===t.target))!==void 0}setup(){this.state.loading=!0,Promise.all([r.settings.translationCompetences(),r.translators.find(this.props.translatorId)]).then(t=>{t[1]||(h.error(i("Unable to load translator information")),this.props.onClose(),this.state.loading=!1),this.state.competences=t[0],this.state.translator=t[1],this.state.allowedCompetences=t[0].filter(s=>!this.translatorHasSkill(s)),this.state.loading=!1})}addSkill(){this.state.potentialSkills.push({competenceId:this.state.allowedCompetences[0].id})}async registerSkills(){this.state.loading=!0;const t=await r.translators.registerSkills(this.props.translatorId,this.state.potentialSkills.map(s=>parseInt(s.competenceId,10)));this.state.loading=!1,t?(h.success(i("Your new skills have been registered")),this.props.onChange()):h.error(i("Unable to register translation skills"))}}e(d,"template",p`
    <Modal active="props.active" loading="languages.loading or state.loading" onClose="props.onClose" title="'Languages'" subtitle="'Your translation skills'" closeButtonText="'Cancel'">
      <div t-if="state.translator" t-att-class="{
        'w-192 grid grid-cols-2': state.translator.skills.length gt 0,
        'w-96': state.translator.skills.length === 0
      }">
        <div class="p-4 flex flex-col items-center" t-if="state.translator.skills.length gt 0">
          <h4 class="font-medium text-slate-700 mb-2">Your current translation skills</h4>
          <TranslationSkills skills="state.translator.skills" />
        </div>
        <div class="p-4 bg-slate-100 flex flex-col items-center">
          <h4 class="font-medium text-slate-700 mb-2">Register a new translation skill</h4>
          <p class="text-sm text-center text-slate-700 mb-4">Please note that translating from a language to another and back is considered two different skills</p>
          <div t-foreach="state.potentialSkills" t-as="skill" t-key="skill_index" class="flex w-full items-center ring ring-slate-300 rounded-sm mb-4">
            <select class="compassion-input text-sm" t-model="skill.competenceId">
              <option t-foreach="state.competences" t-as="competence" t-key="competence.id" t-att-value="competence.id" t-esc="_(competence.source) + ' -> ' + _(competence.target)" t-att-disabled="translatorHasSkill(competence)" />
            </select>
            <Button square="true" level="'secondary'" icon="'trash'" onClick="() => this.state.potentialSkills.splice(skill_index, 1)" />
          </div>
          <div class="flex justify-center">
            <Button onClick="() => this.addSkill()" level="'secondary'" t-if="state.allowedCompetences.length > 0" size="'sm'">Add Skill</Button>
            <p t-else="" class="text-sm text-slate-700 font-semibold">You already have all the translation skills!</p>
          </div>
        </div>
      </div>
      <div t-else="" class="w-96 h-40" />
      <t t-set-slot="footer-buttons">
        <Button onClick="() => this.registerSkills()" disabled="state.potentialSkills.length === 0" color="'compassion'" size="'sm'">Register <span t-esc="state.potentialSkills.length" /> new Skill<span t-esc="state.potentialSkills.length === 1 ? '' : 's'" /></Button>
      </t>
    </Modal>
  `),e(d,"components",{Modal:S,Button:g,TranslationSkills:B}),e(d,"props",{active:{type:Boolean},onClose:{type:Function},onChange:{type:Function},translatorId:{type:Number}});var z=d,k;class f extends u{constructor(){super(...arguments);e(this,"currentTranslator",C());e(this,"_",i);e(this,"state",m({skillLetters:[],savedLetters:void 0,manageSkillsModal:!1,loading:!1}));e(this,"tutorial",I([{text:i('Welcome to the Compassion Translation Platform. This small tutorial will guide you through its features and how it works. You can close it whenever you want to by clicking the "Exit" button.')},{text:((k=this.currentTranslator.data)==null?void 0:k.skills.length)===0?i("You currently have no skills defined, let us begin by registering one or more"):i("It seems you already have translation skills defined, let us see how you can manage them")},{beforeShowPromise:()=>new Promise(t=>{this.state.manageSkillsModal=!0,setTimeout(t,300)}),classes:"no-next no-exit",text:i('This tool allows you to register new skills. If you want to remove some please contact the Compassion team. You can add new skills by clicking the "Add Skill" button. Once done click "Cancel" if you have no changes to do, or "Register new Skills" to validate'),attachTo:{element:".modal",on:"right"}},{id:"post-manage-skills",text:i("Your saved letters will be displayed here along with the ones waiting to be translated. Before picking one, let us review how the translation window works."),attachTo:{element:".waiting-letters-cards",on:"top"},classes:"no-next",buttons:[{classes:"bg-compassion text-white",text:i("Next"),action:()=>{this.tutorial.complete(),console.log("SWAG"),L("/letters/demo-edit-letter")}}]}]))}setup(){this.refresh().then(()=>{M(this.tutorial)})}async refresh(){this.state.loading=!0,this.currentTranslator.data||this.currentTranslator.refresh(),await Promise.all([this.fetchLetters(),this.fetchSaved()]),this.state.loading=!1}async onSkillsChange(){this.state.manageSkillsModal=!1,this.state.loading=!0,await this.currentTranslator.refresh(),this.refresh(),this.postSkillsModal()}async closeSkillsModal(){this.state.manageSkillsModal=!1,this.postSkillsModal()}async postSkillsModal(){var t;_()&&((t=this.tutorial.getCurrentStep())==null||t.hide(),setTimeout(()=>{var s;return(s=this.tutorial.getById("post-manage-skills"))==null?void 0:s.show()},300))}async fetchSaved(){!this.currentTranslator.data||(this.state.savedLetters=await r.letters.list({sortBy:"priority",sortOrder:"asc",pageNumber:0,pageSize:5,search:[{column:"translatorId",term:`${this.currentTranslator.data.translatorId}`},{column:"status",term:"in progress"}]}))}async fetchLetters(){if(!this.currentTranslator.data)return;const t=await Promise.all(this.currentTranslator.data.skills.map(async s=>{const o=await r.letters.list({sortBy:"priority",sortOrder:"asc",pageSize:5,pageNumber:0,search:[{column:"status",term:"to do"},{column:"source",term:s.source},{column:"target",term:s.target}]});return{skill:s,total:o.total,letters:o.data}}));this.state.skillLetters=t.sort((s,o)=>s.skill.verified?1:o.skill.verified?-1:0)}}e(f,"template",R),e(f,"components",{Button:g,TranslationCard:P,LanguagesPickModal:z,BlurLoader:T});export{f as default};
