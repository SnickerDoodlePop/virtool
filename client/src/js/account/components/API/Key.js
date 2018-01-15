import React from "react";
import Moment from "moment";
import PropTypes from "prop-types";
import { isEqual, reduce } from "lodash";
import { ButtonToolbar, Col, Row } from "react-bootstrap";

import APIPermissions from "./Permissions";
import { Button, ListGroupItem, RelativeTime } from "../../../base/index";

export default class APIKey extends React.Component {

    constructor (props) {
        super(props);

        this.state = {
            in: false,
            changed: false,
            permissions: props.apiKey.permissions
        };
    }

    static propTypes = {
        apiKey: PropTypes.object,
        permissions: PropTypes.object,
        onRemove: PropTypes.func,
        onUpdate: PropTypes.func
    };

    toggleIn = () => {
        const state = {
            in: !this.state.in
        };

        if (this.state.in) {
            state.permissions = this.props.apiKey.permissions;
        }

        this.setState(state);
    };

    handlePermissionChange = (key, value) => {
        const update = {};
        update[key] = value;
        const permissions = {...this.state.permissions, update};
        this.setState({
            changed: !isEqual(permissions, this.props.apiKey.permissions),
            permissions
        });
    };

    render () {
        let lower;
        let closeButton;

        if (this.state.in) {
            lower = (
                <div>
                    <Row>
                        <Col xs={12}>
                            <APIPermissions
                                style={{marginTop: "15px"}}
                                userPermissions={this.props.permissions}
                                keyPermissions={this.state.permissions}
                                onChange={this.handlePermissionChange}
                            />
                        </Col>
                    </Row>
                    <Row>
                        <Col xs={12}>
                            <ButtonToolbar className="pull-right">
                                <Button
                                    bsStyle="danger"
                                    icon="remove"
                                    onClick={() => this.props.onRemove(this.props.apiKey.id)}
                                >
                                    Remove
                                </Button>
                                <Button
                                    bsStyle="primary"
                                    icon="floppy"
                                    onClick={() => this.props.onUpdate(this.props.apiKey.id, this.state.permissions)}
                                    disabled={!this.state.changed}
                                >
                                    Update
                                </Button>
                            </ButtonToolbar>
                        </Col>
                    </Row>
                </div>
            );

            closeButton = (
                <button type="button" className="close" onClick={this.toggleIn}>
                    <span>×</span>
                </button>
            );
        }

        const permissionCount = reduce(this.props.apiKey.permissions, (result, value) => result + (value ? 1 : 0), 0);

        return (
            <ListGroupItem key={this.props.apiKey.id} className="spaced" onClick={this.state.in ? null : this.toggleIn}>
                <Row>
                    <Col xs={4}>
                        <strong>{this.props.apiKey.name}</strong>
                    </Col>

                    <Col xs={4}>
                        <span>{permissionCount} perm</span>
                        <span className="hidden-xs hidden-sm">ission</span>{permissionCount === 1 ? null : "s"}
                    </Col>

                    <Col xsHidden smHidden md={3}>
                        Created <RelativeTime time={this.props.apiKey.created_at} />
                    </Col>
                    <Col mdHidden lgHidden xs={3}>
                        {Moment(this.props.apiKey.created_at).format("YY-MM-DD")}
                    </Col>

                    <Col xs={1}>
                        {closeButton}
                    </Col>
                </Row>

                {lower}
            </ListGroupItem>
        );
    }
}
