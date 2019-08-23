import { action } from "mobx";
import * as React from "react";

import { app } from "./app";
import styles from "./index.scss";

type KeyActionGroup = "plan" | "persons" | "actions";

interface KeyAction {
  group: KeyActionGroup;
  description: string;
  action: () => void;
}

const actions: { [key: string]: KeyAction } = {
  h: {
    group: "plan",
    description: "Venstre",
    action: () => {
      // plan move left
      if (app.focusPlanCoordinates === null) app.focusPlanCoordinates = [0, 0];
      else if (app.focusPlanCoordinates[1] !== 0)
        app.focusPlanCoordinates[1] -= 1;
    }
  },
  j: {
    group: "plan",
    description: "Ned",
    action: () => {
      // plan move down
      if (app.focusPlanCoordinates === null) app.focusPlanCoordinates = [0, 0];
      else if (app.focusPlanCoordinates[0] !== app.timeNames.length - 1)
        app.focusPlanCoordinates[0] += 1;
    }
  },
  k: {
    group: "plan",
    description: "Op",
    action: () => {
      // plan move up
      if (app.focusPlanCoordinates === null) app.focusPlanCoordinates = [0, 0];
      else if (app.focusPlanCoordinates[0] !== 0)
        app.focusPlanCoordinates[0] -= 1;
    }
  },
  l: {
    group: "plan",
    description: "Højre",
    action: () => {
      // plan move right
      if (app.focusPlanCoordinates === null) app.focusPlanCoordinates = [0, 0];
      else if (app.focusPlanCoordinates[1] !== app.locationNames.length - 1)
        app.focusPlanCoordinates[1] += 1;
    }
  },
  w: {
    group: "persons",
    description: "Op",
    action: () => {
      // personlist move up
      if (app.focusPersonIndex === null) app.focusPersonIndex = 0;
      else
        app.focusPersonIndex =
          app.focusPersonIndex === 0
            ? app.persons.length - 1
            : app.focusPersonIndex - 1;
    }
  },
  s: {
    group: "persons",
    description: "Ned",
    action: () => {
      // personlist move down
      if (app.focusPersonIndex === null) app.focusPersonIndex = 0;
      else
        app.focusPersonIndex =
          app.focusPersonIndex === app.persons.length - 1
            ? 0
            : app.focusPersonIndex + 1;
    }
  },
  a: {
    group: "actions",
    description: "Tilføj til vagt",
    action: () => {
      // Add person in focus to workslot in focus
      app.addPersonInFocusToSlot();
    }
  },
  r: {
    group: "actions",
    description: "Fjern fra vagt",
    action: () => {
      // Remove person in focus to workslot in focus
      app.removePersonInFocusFromSlot();
    }
  },
  e: {
    group: "actions",
    description: "Gør ansvarlig/uansvarlig",
    action: () => {
      if (app.focusPersonIndex !== null && app.focusPlanCoordinates !== null) {
        const [t, l] = app.focusPlanCoordinates;
        const i = app.focusPersonIndex;
        const supervisorIndex = app.supervisorExists(t, l);
        if (supervisorIndex === null) {
          app.addAsSupervisor(i, t, l);
        } else if (supervisorIndex === i) {
          app.removeAsSupervisor(i, t, l);
        }
      }
    }
  },
  c: {
    group: "actions",
    description: "Luk/åben vagt",
    action: () => {
      // Close or reopen workslot
      if (app.focusPlanCoordinates !== null) {
        const [t, l] = app.focusPlanCoordinates;
        if (
          app.closedWorkslots.some(coords => coords[0] === t && coords[1] === l)
        ) {
          app.openWorkslot(t, l);
        } else {
          app.closeWorkslot(t, l);
        }
      }
    }
  }
};

class KeyHandler {
  private groupHelp(group: KeyActionGroup) {
    return Object.entries(actions)
      .filter(([_k, a]) => a.group == group)
      .map(([k, a]) => (
        <li key={k}>
          {k}: {a.description}
        </li>
      ));
  }

  shortcutHelp() {
    return (
      <div className={styles.shortcutHelp}>
        <h2>Genvejstaster:</h2>
        <b>Plan navigation:</b>
        <ul>{this.groupHelp("plan")}</ul>
        <b>Personliste navigation:</b>
        <ul>{this.groupHelp("persons")}</ul>
        <b>Handlinger:</b>
        <ul>{this.groupHelp("actions")}</ul>
      </div>
    );
  }

  @action
  onKeyPress(key: string) {
    const action = actions[key];
    if (action == null) return;
    action.action();
  }
}

export const keyHandler = new KeyHandler();
