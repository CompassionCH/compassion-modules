/* Copyright 2026 Compassion CH (http://www.compassion.ch)
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */
import { FsFolder } from "@fs_folder/fs_folder/fs_folder.esm";
import { patch } from "@web/core/utils/patch";

// The fs_folder widget ignores the readonly attribute: hide the actions that
// change the folder (the server refuses them anyway without write access).
patch(FsFolder.prototype, {
  get moreActionDef() {
    return this.props.readonly ? [] : super.moreActionDef;
  },
  async onDropFile(event) {
    if (this.props.readonly) {
      return;
    }
    return super.onDropFile(event);
  },
});
