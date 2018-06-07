import React from "react";
import { Alert, ButtonToolbar, Modal, ListGroup, Col, Badge } from "react-bootstrap";
import { connect } from "react-redux";
import { upperFirst, find, map } from "lodash-es";
import ReferenceForm from "./Form";
import { Button, ListGroupItem, NoneFound, RelativeTime } from "../../base";
import { cloneReference } from "../actions";
import { clearError } from "../../errors/actions";

const ReferenceSelect = ({ references, onSelect, selected }) => (
    <div>
        <label className="control-label">Source Reference</label>
        {references.length
            ? (
                <ListGroup style={{maxHeight: "84px", overflowY: "auto"}}>
                    {map(references, reference =>
                        <ListGroupItem
                            key={reference.id}
                            onClick={() => onSelect(reference.id)}
                            active={selected === reference.id}
                        >
                            <Col xs={5}>
                                <strong>{reference.name}</strong>
                            </Col>
                            <Col xs={6}>
                                <span className="text-muted" style={{fontSize: "10px"}}>
                                    Created <RelativeTime time={reference.created_at} /> by {reference.user.id}
                                </span>
                            </Col>
                            <Col xs={1}>
                                <Badge>{reference.otu_count}</Badge>
                            </Col>
                        </ListGroupItem>
                    )}
                </ListGroup>
            ) : <NoneFound noun="source references" />
        }
    </div>
);

const getInitialState = (refId, refArray) => {

    const originalRef = find(refArray, { id: refId });

    if (originalRef) {
        return {
            reference: originalRef.id,
            name: `Clone of ${originalRef.name}`,
            description: originalRef.description,
            dataType: originalRef.data_type || "",
            organism: originalRef.organism,
            isPublic: originalRef.public,
            errorName: "",
            errorDataType: ""
        };
    }

    return {
        reference: "",
        name: "",
        description: "",
        dataType: "",
        organism: "",
        isPublic: false,
        errorName: "",
        errorDataType: ""
    };
};

class CloneReference extends React.Component {

    constructor (props) {
        super(props);
        this.state = getInitialState(this.props.refId, this.props.refDocuments);
    }

    handleChange = (e) => {
        const { name, value } = e.target;

        if (name === "name" || name === "dataType") {
            const errorType = `error${upperFirst(e.target.name)}`;

            this.setState({
                [name]: value,
                [errorType]: ""
            });
        } else if (name === "reference") {
            this.setState({
                [name]: value
            });
        } else {
            this.setState({
                [name]: value
            });
        }
    };

    handleSelect = (refId) => {
        this.setState(getInitialState(refId, this.props.refDocuments));
    };

    handleSubmit = (e) => {
        e.preventDefault();

        if (!this.state.name.length) {
            this.setState({ errorName: "Required Field" });
        }

        if (!this.state.dataType.length) {
            this.setState({ errorDataType: "Required Field" });
        }

        if (this.state.name.length && this.state.dataType.length) {
            this.props.onSubmit(
                this.state.name,
                this.state.description,
                this.state.dataType,
                this.state.organism,
                this.state.isPublic,
                this.state.reference
            );
        }

    };

    toggleCheck = () => {
        this.setState({ isPublic: !this.state.isPublic });
    };

    render () {

        return (
            <React.Fragment>
                <Modal.Body>
                    <Alert bsStyle="info">
                        <strong>
                            Clone an existing reference.
                        </strong>
                    </Alert>
                    <ReferenceSelect
                        references={this.props.refDocuments}
                        onSelect={this.handleSelect}
                        selected={this.state.reference}
                    />
                    <ReferenceForm
                        state={this.state}
                        onChange={this.handleChange}
                        toggle={this.toggleCheck}
                    />
                </Modal.Body>

                <Modal.Footer>
                    <ButtonToolbar className="pull-right">
                        <Button
                            icon="save"
                            type="submit"
                            bsStyle="primary"
                            onClick={this.handleSubmit}
                            disabled={!this.props.refDocuments.length}
                        >
                            Clone
                        </Button>
                    </ButtonToolbar>
                </Modal.Footer>
            </React.Fragment>
        );
    }

}

const mapStateToProps = state => ({
    refId: state.router.location.state.refId,
    refDocuments: state.references.documents
});

const mapDispatchToProps = dispatch => ({

    onSubmit: (name, description, dataType, organism, isPublic, refId) => {
        dispatch(cloneReference(name, description, dataType, organism, isPublic, refId));
    },

    onClearError: (error) => {
        dispatch(clearError(error));
    }

});

export default connect(mapStateToProps, mapDispatchToProps)(CloneReference);
