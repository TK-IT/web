import { action, configure } from "mobx";
import { observer } from "mobx-react";
import * as React from "react";
import * as ReactDOM from "react-dom";

import { app } from "./app";
import { planGenerator } from "./generator";
import styles from "./index.scss";
import { keyHandler } from "./keyhandler";
import { parser } from "./parser";
import { classNames } from "./util";

@observer
class AppComponent extends React.Component<{}, {}> {
  componentDidMount() {
    this.parsePlanTemplateString(app.planTemplateString);
    this.parsePersonsString(app.personsString);
  }

  render() {
    return (
      <div>
        <div
          className={classNames({
            [styles.hasFocusedPerson]: app.focusPersonIndex != null
          })}
        >
          <b>Plan</b>
          <div>
            <textarea
              value={app.planTemplateString}
              onChange={e => this.parsePlanTemplateString(e.target.value)}
            />
          </div>
          <div>
            <b>Personer</b>
            <div>
              <textarea
                value={app.personsString}
                onChange={e => this.parsePersonsString(e.target.value)}
              />
            </div>
          </div>
          <div className={styles.editor}>
            <div className={styles.personsList}>
              <PersonList />
            </div>
            <div className={styles.plan}>
              <Plan />
            </div>
            <div className={styles.controlPanel}>
              <ControlPanel />
            </div>
          </div>
          <button onClick={_e => planGenerator.generatePlan()}>
            Generer Barplan
          </button>
          <button onClick={_e => this.downloadCSV()}>Download som CSV</button>
          <button onClick={_e => this.downloadLaTeX()}>
            Download som LaTeX
          </button>
        </div>
      </div>
    );
  }

  downloadLaTeX(): void {
    const fileContents = parser.parsePlanToLaTeXString();
    const fileName = "plan_data.tex";
    this.downloadFile(fileContents, fileName);
  }

  downloadCSV(): void {
    const fileContents = parser.parsePlanToCSVString();
    const fileName = "plan.csv";
    this.downloadFile(fileContents, fileName);
  }

  downloadFile(fileContent: string, fileName: string) {
    const a = document.createElement("a");
    /*  
        There can be some encoding problems in the conversion from unicode
        to base64. A possible solution to the problem can be found at:
        https://developer.mozilla.org/en-US/docs/Web/API/WindowOrWorkerGlobalScope/btoa
    */
    const dataURI = "data:text/plain; base64," + btoa(fileContent);
    a.href = dataURI;
    a["download"] = fileName;

    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  @action
  parsePlanTemplateString(s: string) {
    app.planTemplateString = s;
    const rows = s.split("\n");
    app.locationNames = rows[0].trim().split("\t");
    app.timeNames = rows.slice(1).map(row => row.split("\t")[0].trim());
  }

  @action
  parsePersonsString(s: string) {
    app.personsString = s;
    const rows = s.split("\n");
    app.persons = rows
      .map(row => row.split("\t")[0].trim())
      .filter(name => name != "");
    while (app.personsWorkslots.length < app.persons.length) {
      app.personsWorkslots.push([]);
    }
  }
}

@observer
class PersonList extends React.Component<{}, {}> {
  render() {
    return (
      <table>
        <tbody>
          {app.persons.map((name, i) => (
            <tr>
              <td
                onClick={e => {
                  this.onClick(i);
                  e.stopPropagation();
                }}
                className={
                  app.focusPersonIndex === i ? styles.personInFocus : ""
                }
              >
                {name}
              </td>
              {app.locationNames.map((_loc, l) => (
                <td>{this.numberOfTimeslotsOnLocation(l, i)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  @action
  onClick(personIndex: number) {
    app.focusPersonIndex =
      app.focusPersonIndex === personIndex ? null : personIndex;
  }

  numberOfTimeslotsOnLocation(l: number, i: number) {
    return app.personsWorkslots[i].filter(coord => coord[1] === l).length;
  }
}

@observer
class Plan extends React.Component<{}, {}> {
  render() {
    return (
      <table>
        <tbody>
          <tr>
            <td></td>
            {app.locationNames.map(loc => (
              <td>{loc}</td>
            ))}
          </tr>
          {app.timeNames.map((time, t) => (
            <tr>
              <td>{time}</td>
              {app.locationNames.map((_loc, l) => (
                <td
                  onClick={() => this.onClick(t, l)}
                  className={classNames({
                    [styles.personInFocus]: app.isFocusedPersonInSlot(t, l),
                    [styles.timeSlotInFocus]: app.isTimeSlotInFocus(t, l),
                    [styles.doubleBooking]: this.doubleBookingHasOccurred(t, l) // Will overwrite personInFocus
                  })}
                >
                  {this.workslotContentDecision(t, l)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  @action
  onClick(t: number, l: number) {
    if (app.focusPersonIndex === null || app.isFocusedPersonInSlot(t, l)) {
      app.focusPlanCoordinates = app.isTimeSlotInFocus(t, l) ? null : [t, l];
      return;
    }
    app.addPersonToSlot(t, l, app.focusPersonIndex);
    app.focusPersonIndex = null;
  }

  doubleBookingHasOccurred(t: number, l: number): boolean {
    for (let i = 0; i < app.persons.length; i++) {
      const timeSlotList = app.personsWorkslots[i].filter(
        slot => slot[0] === t
      );
      if (timeSlotList.length > 1 && timeSlotList.some(slot => slot[1] === l)) {
        return true;
      }
    }
    return false;
  }

  workslotContentDecision(t: number, l: number) {
    if (app.workslotClosed(t, l)) {
      const button = (
        <button
          onClick={e => {
            app.openWorkslot(t, l);
            e.stopPropagation();
          }}
        >
          Åben
        </button>
      );
      return (
        <div className={styles.workslotWorkerList}>
          <div className={styles.emptyWorkslotButtons}>
            <b>-</b>
            <div className={styles.buttons}>{button}</div>
          </div>
        </div>
      );
    } else return this.listWorkers(t, l);
  }

  listWorkers(t: number, l: number) {
    const workersList: JSX.Element[] = [];
    app.persons.forEach((personName, i) => {
      app.personsWorkslots[i].forEach(slot => {
        if (slot[0] === t && slot[1] === l) {
          const person = (
            <PersonWorkslot
              key={i}
              name={personName}
              supervisor={slot[2]}
              onAddSupervisor={() => app.addAsSupervisor(i, t, l)}
              onRemoveSupervisor={() => app.removeAsSupervisor(i, t, l)}
              onRemove={() => app.removePerson(i, t, l)}
            />
          );
          if (slot[2]) {
            // Put supervisor first
            workersList.unshift(person);
          } else {
            workersList.push(person);
          }
        }
      });
    });
    if (!workersList.length) {
      const button = (
        <button
          onClick={e => {
            app.closeWorkslot(t, l);
            e.stopPropagation();
          }}
        >
          Luk
        </button>
      );
      workersList.push(
        <div className={styles.emptyWorkslotButtons}>
          <div className={styles.buttons}>{button}</div>
        </div>
      );
    }
    return <div className={styles.workslotWorkerList}>{workersList}</div>;
  }
}

interface PersonWorkslotProps {
  name: string;
  supervisor: boolean;
  onAddSupervisor: () => void;
  onRemoveSupervisor: () => void;
  onRemove: () => void;
}

@observer
class PersonWorkslot extends React.Component<PersonWorkslotProps, {}> {
  render() {
    return (
      <div
        className={classNames({ [styles.supervisor]: this.props.supervisor })}
      >
        {this.props.name}
        {this.renderButtons()}
      </div>
    );
  }

  renderButtons() {
    return (
      <div className={styles.buttons}>
        {this.renderSupervisorButton()}
        {this.renderRemoveButton()}
      </div>
    );
  }

  renderSupervisorButton() {
    if (this.props.supervisor)
      return (
        <button
          onClick={e => {
            this.props.onRemoveSupervisor();
            e.stopPropagation();
          }}
        >
          -
        </button>
      );
    else
      return (
        <button
          onClick={e => {
            this.props.onAddSupervisor();
            e.stopPropagation();
          }}
        >
          +
        </button>
      );
  }

  renderRemoveButton() {
    return (
      <button
        onClick={e => {
          this.props.onRemove();
          e.stopPropagation();
        }}
      >
        X
      </button>
    );
  }
}

@observer
class ControlPanel extends React.Component<{}, {}> {
  render() {
    return (
      <>
        <div>
          {this.heading()}
          {this.buttons()}
        </div>
        <div>{keyHandler.shortcutHelp()}</div>
      </>
    );
  }

  heading() {
    if (app.focusPlanCoordinates == null) {
      return "";
    }
    const [t, l] = app.focusPlanCoordinates;
    return (
      <b>
        {app.locationNames[l]} kl. {app.timeNames[t]}
      </b>
    );
  }

  buttons() {
    if (app.focusPlanCoordinates == null) {
      return <></>;
    }
    const [t, l] = app.focusPlanCoordinates;
    if (app.workslotClosed(t, l)) {
      return (
        <div>
          <button onClick={_e => this.openWorkslot()}>Genåben vagt</button>
        </div>
      );
    } else {
      return (
        <>
          <div>{this.addOrRemoveButton()}</div>
          <div>{this.supervisorButton()}</div>
          <div>{this.workstationClosedButtons()}</div>
        </>
      );
    }
  }

  workstationClosedButtons() {
    if (app.focusPlanCoordinates == null) {
      return <></>;
    }
    let button = <></>;
    const [t, l] = app.focusPlanCoordinates;
    if (!app.workslotClosed(t, l)) {
      button = (
        <button onClick={_e => this.closeWorkslot()}>
          Lad denne vagt være lukket
        </button>
      );
    }
    return button;
  }

  @action
  closeWorkslot() {
    if (app.focusPlanCoordinates != null) {
      const [t, l] = app.focusPlanCoordinates;
      app.closeWorkslot(t, l);
    }
  }

  @action
  openWorkslot() {
    if (app.focusPlanCoordinates != null) {
      const [t, l] = app.focusPlanCoordinates;
      app.openWorkslot(t, l);
    }
  }

  supervisorButton() {
    if (app.focusPlanCoordinates == null) {
      return <></>;
    }
    let button = <></>;
    const [t, l] = app.focusPlanCoordinates;
    app.persons.forEach((_person, i) => {
      app.personsWorkslots[i].forEach(slot => {
        if (slot[0] === t && slot[1] === l && app.focusPersonIndex == i) {
          if (slot[2] === false) {
            button = (
              <button onClick={_e => this.addAsSupervisor(i)}>
                Gør til ansvarlig
              </button>
            );
          } else if (slot[2] === true) {
            button = (
              <button onClick={_e => this.removeAsSupervisor(i)}>
                Gør uansvarlig
              </button>
            );
          }
        }
      });
    });
    return button;
  }

  @action
  removeAsSupervisor(personIndex: number): void {
    if (app.focusPlanCoordinates != null) {
      const [t, l] = app.focusPlanCoordinates;
      app.removeAsSupervisor(personIndex, t, l);
    }
  }

  @action
  addAsSupervisor(personIndex: number): void {
    if (app.focusPlanCoordinates != null) {
      const [t, l] = app.focusPlanCoordinates;
      app.addAsSupervisor(personIndex, t, l);
    }
  }

  addOrRemoveButton() {
    if (app.focusPlanCoordinates != null) {
      if (
        app.isFocusedPersonInSlot(
          app.focusPlanCoordinates[0],
          app.focusPlanCoordinates[1]
        )
      ) {
        return (
          <button onClick={_e => app.removePersonInFocusFromSlot()}>
            Fjern fra vagt
          </button>
        );
      } else if (app.focusPersonIndex != null) {
        return (
          <button onClick={_e => app.addPersonInFocusToSlot()}>
            Tilføj til vagt
          </button>
        );
      }
    }
    return "";
  }
}

configure({ enforceActions: "always", computedRequiresReaction: true });
document.addEventListener("keypress", e => keyHandler.onKeyPress(e.key));
ReactDOM.render(<AppComponent />, document.getElementById("root"));
