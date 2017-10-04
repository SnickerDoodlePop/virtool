/**
 * @license
 * The MIT License (MIT)
 * Copyright 2015 Government of Canada
 *
 * @author
 * Ian Boyes
 *
 * @exports UserSettings
 */

import React from "react";
import { connect } from "react-redux";
import { Panel, ListGroup, ListGroupItem } from "react-bootstrap";

import { updateAccountSettings } from "../actions";
import { AlgorithmSelect, Checkbox, Flex, FlexItem, Icon } from "../../base";


class AccountSettings extends React.Component {

    constructor (props) {
        super(props);
    }

    render () {
        const settings = this.props.account.settings;

        return (
            <div>
                <Panel header="User Interface">
                    <ListGroup fill>
                        <ListGroupItem>
                            <Flex>
                                <FlexItem>
                                    <Checkbox
                                        checked={settings.show_ids}
                                        onClick={(e) => this.props.onUpdateSetting("show_ids", e.target.value)}
                                    />
                                </FlexItem>
                                <FlexItem pad={10}>
                                    <div>Show Unique ID Fields</div>
                                    <small>
                                        Show the unique database IDs for Virtool records where possible. This is not
                                        required for normal use, but is useful for debugging.
                                    </small>
                                </FlexItem>
                            </Flex>
                        </ListGroupItem>
                    </ListGroup>
                </Panel>

                <Panel header="Quick Analyze">
                    <ListGroup fill>
                        <ListGroupItem>
                            <Flex>
                                <FlexItem>
                                    <Checkbox
                                        checked={settings.skip_quick_analyze_dialog}
                                        onClick={(e) => this.props.onUpdateSetting(
                                            "skip_quick_analyze_dialog",
                                            e.target.value
                                        )}
                                    />
                                </FlexItem>
                                <FlexItem pad={10}>
                                    <div>Skip Dialog</div>
                                    <small>
                                        Allow samples to be analyzed with a single click of
                                        &nbsp;<Icon bsStyle="success" name="bars" /> using a preconfigured algorithm.
                                        The algorithm selection dialog is not shown.
                                    </small>

                                    <div style={{marginTop: "7px"}}>
                                        <AlgorithmSelect
                                            value={settings.quick_analyze_algorithm}
                                            noLabel={true}
                                            onChange={(e) => this.props.onUpdateSetting(
                                                "quick_analyze_algorithm",
                                                e.target.value
                                            )}
                                        />
                                    </div>
                                </FlexItem>
                            </Flex>
                        </ListGroupItem>
                    </ListGroup>
                </Panel>
            </div>
        );
    }
}

const mapStateToProps = (state) => {
    return {
        account: state.account
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        onUpdateSetting: (key, value) => {
            let update = {};
            update[key] = value;
            dispatch(updateAccountSettings(update));
        }
    };
};

const Container = connect(mapStateToProps, mapDispatchToProps)(AccountSettings);

export default Container;
