var u=Object.defineProperty;var v=(a,o,e)=>o in a?u(a,o,{enumerable:!0,configurable:!0,writable:!0,value:e}):a[o]=e;var t=(a,o,e)=>(v(a,typeof o!="symbol"?o+"":o,e),e);import{C as d,x as r,B as c,T as h,M as p,u as f,_ as i,n as g,R as y}from"./index.79c05fa8.js";const b={letter:{type:Object},onAddParagraph:{type:Function,optional:!0},onAddPageBreak:{type:Function,optional:!0},onRemove:{type:Function,optional:!0},onMove:{type:Function,optional:!0}};class n extends d{constructor(){super(...arguments);t(this,"state",f({}));t(this,"_",i)}addParagraph(){this.props.onAddParagraph()}addPageBreak(){this.props.onAddPageBreak()}move(e,s){this.props.onMove(e,s)}remove(e){this.props.onRemove(e)}openSource(e){const s=this.props.letter.translatedElements.find(m=>m.id===e);!s||s.type!=="paragraph"?g.error(i("Unable to find element")):this.state.modalSourceElem=s.source}}t(n,"template",r`
    <div id="content-editor">
      <div t-foreach="this.props.letter.translatedElements" t-as="element" t-key="element.id" class="mx-4 mb-4 border border-solid transition-all editor-element" t-att-class="{
        'border-compassion ring ring-2 ring-compassion ring-opacity-30 ring-offset-0': state.hovered === element.id,
        'border-transparent': state.hovered !== element.id,
      }">
        <div t-if="element.type == 'pageBreak'" class="flex">
            <div class="relative bg-slash flex-1 flex justify-center items-center" t-att-class="{'py-2': element.readonly}">
              <span class="text-slate-500 font-medium text-xs">Page Break</span>
            </div>
          <div class="flex flex-col justify-center gap-2 ml-2">
            <t t-if="element.readonly" >
              <Tippy placement="'left'" content="_('This page break is locked and cannot be removed, it is part of the original content')">
                <Button square="true" disabled="true" level="'secondary'" icon="'lock'" class="'editor-paragraph-locked'" />
              </Tippy>
            </t>
            <div t-if="!element.readonly" t-on-mouseenter="() => state.hovered = element.id" t-on-mouseleave="() => state.hovered = undefined">
              <Button square="true" color="'red'" level="'secondary'" icon="'trash'" onClick="() => this.remove(element.id)" />
            </div>
          </div>
        </div>
        <div t-if="element.type == 'paragraph'" class="flex editor-paragraph">
          <div class="bg-white shadow-xl relative z-10 grid grid-cols-6 flex-1">
            <div class="col-span-4 py-4 px-4 editor-paragraph-content">
              <h4 class="font-medium text-slate-700 mb-2">Translated Content</h4>
              <textarea class="compassion-input w-full h-32 text-xs flex" t-model="element.content" />
            </div>
            <div class="col-span-2 bg-slate-50 p-4 editor-paragraph-comment">
              <h4 class="font-medium text-slate-700 mb-2">Comment</h4>
              <textarea class="compassion-input w-full h-32 text-xs flex" t-model="element.comments" />
            </div>
          </div>
          <div class="flex flex-col justify-center gap-2 ml-2 buttons-element-state">
            <div t-if="!element.readonly" t-on-mouseenter="() => state.hovered = element.id" t-on-mouseleave="() => state.hovered = undefined">
              <Button square="true" level="'secondary'" t-if="!element_first and !this.props.letter.translatedElements[element_index - 1].readonly" icon="'angle-up'" t-on-click="() => this.move(element.id, -1)" />
            </div>
            <div t-if="!element.readonly" t-on-mouseenter="() => state.hovered = element.id" t-on-mouseleave="() => state.hovered = undefined">
              <Button square="true" color="'red'" level="'secondary'" icon="'trash'" t-on-click="() => this.remove(element.id)" />
            </div>
            <div t-if="!element.readonly" t-on-mouseenter="() => state.hovered = element.id" t-on-mouseleave="() => state.hovered = undefined">
              <Button square="true" level="'secondary'" t-if="!element_last and !this.props.letter.translatedElements[element_index + 1].readonly" icon="'angle-down'" t-on-click="() => this.move(element.id, 1)" />
            </div>
            <div t-if="element.readonly" class="flex justify-center">
              <Tippy placement="'left'" content="_('This paragraph is locked and cannot be removed, it is part of the original content')">
                <Button disabled="true" level="'secondary'" icon="'lock'" square="true" />
              </Tippy>
            </div>
            <t t-if="element.readonly">
              <Tippy placement="'left'" content="_('Open Paragraph source text')" delay="200">
                <Button title="'Open source text'" square="true" level="'secondary'" icon="'eye'" t-on-click="() => this.openSource(element.id)" />
              </Tippy>
            </t>
          </div>
        </div>
      </div>
      <div class="flex justify-center mt-4">
        <div class="flex gap-2 buttons-add-elements">
          <Button size="'sm'" icon="'plus'" level="'secondary'" t-on-click="addParagraph">Paragraph</Button>
          <Button size="'sm'" icon="'plus'" level="'secondary'" t-on-click="addPageBreak">PageBreak</Button>
        </div>
      </div>
    </div>
    <Modal active="state.modalSourceElem !== undefined" title="'Source Text'" onClose="() => this.state.modalSourceElem = undefined">
      <div class="p-4 w-128">
        <p class="text-sm text-slate-800" t-if="state.modalSourceElem and state.modalSourceElem.trim() !== ''" t-esc="state.modalSourceElem" />
        <p t-else="" class="italic text-slate-600 font-light">No source text available</p>
      </div>
    </Modal>
  `),t(n,"props",b),t(n,"components",{Button:c,Tippy:h,Modal:p});var B=r`<LetterViewer letter="state.letter" letterId="props.letterId" loading="state.loading" smallLoading="state.saveLoading and state.internalLoading !== true">
  <!-- action bar buttons -->
  <t t-set-slot="action-buttons" t-slot-scope="buttons">
    <Button color="'red'" level="'secondary'" icon="'triangle-exclamation'" onClick="() => state.signalProblemModal = true" size="'sm'" class="'action-problem'">Signal a Problem</Button>
    <Button color="'green'" onClick="() => this.save()" icon="'floppy-disk'" level="'secondary'" size="'sm'" class="'action-save'">Save</Button>
    <Button color="'compassion'" onClick="() => this.submit()" icon="'paper-plane'" size="'sm'" class="'action-submit'">Submit</Button>
  </t>

  <!-- signal problem modal in unsafe slot (no letter) -->
  <t t-set-slot="unsafe">
    <SignalProblem active="state.signalProblemModal" letterId="props.letterId" onClose="() => state.signalProblemModal = false" />
  </t>

  <!-- loader for letter loading -->
  <t t-set-slot="right-pane">
    <BlurLoader active="state.internalLoading" />
  </t>

  <t t-set-slot="content" t-slot-scope="scope">
    <LetterSubmittedModal active="state.letterSubmitted" letter="scope.letter" />
    <ContentEditor letter="scope.letter" onAddParagraph.bind="addParagraph" onAddPageBreak.bind="addPageBreak" onRemove.bind="remove" onMove.bind="move"/>
  </t>
</LetterViewer>`;class l extends d{}t(l,"template",r`
    <Modal active="props.active" title="'Thank You'" empty="true">
      <div class="w-128">
        <img src="/logo_simple.png" class="w-16 mx-auto block mt-8" />
        <h1 class="text-center text-3xl font-light text-slate-700 mt-4">Thank You!</h1>
        <p class="text-center text-slate-600 p-4">
          Thank you for your contribution. Your letter will be reviewed before being sent,
          bringing a smile on the face of both <t t-esc="props.letter.child.preferredName" /> and <t t-esc="props.letter.sponsor.preferredName" />.<br/>
          <span class="block font-semibold pt-4">Thank you in the name of Compassion Switzerland, we are glad to have you in the team!</span>
        </p>
        <div class="flex justify-center mt-4 p-4 border-t border-solid border-slate-300 ">
          <RouterLink to="'/'">
            <Button size="'sm'" level="'secondary'" color="'compassion'" icon="'home'">Bring me back to Home</Button>
          </RouterLink>
        </div>
      </div>
    </Modal>
  `),t(l,"props",["active","letter"]),t(l,"components",{Modal:p,RouterLink:y,Button:c});export{n as C,l as L,B as t};
