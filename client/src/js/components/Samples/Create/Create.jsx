/**
 * @license
 * The MIT License (MIT)
 * Copyright 2015 Government of Canada
 *
 * @author
 * Ian Boyes
 *
 * @exports SamplesImport
 *
 */

'use strict';

var React = require('react');
var ListGroup = require('react-bootstrap/lib/ListGroup');
var Alert = require('react-bootstrap/lib/Alert');
var Input = require('react-bootstrap/lib/Input');
var Panel = require('react-bootstrap/lib/Panel');
var Label = require('react-bootstrap/lib/Label');
var Row = require('react-bootstrap/lib/Row');
var Col = require('react-bootstrap/lib/Col');
var Modal = require('react-bootstrap/lib/Modal');

var ReadSelector = require('./Reads.jsx');
var Form = require('./Form.jsx');
var Icon = require('virtool/js/components/Base/Icon.jsx');
var PushButton = require('virtool/js/components/Base/PushButton.jsx');

/**
 * A main view for importing samples from FASTQ files. Importing starts an import job on the server.
 *
 * @class
 */
var SamplesImport = React.createClass({

    propTypes: {
        show: React.PropTypes.bool.isRequired,
        onHide: React.PropTypes.func.isRequired
    },

    getInitialState: function () {
        return {
            selected: [],

            nameExistsError: false,
            nameEmptyError: false,
            readError: false
        };
    },


    select: function (selected) {
        this.setState({
            selected: selected
        });
    },

    /**
     * Send a request to the server
     *
     * @param event {object} - the submit event
     */
    handleSubmit: function (event) {
        event.preventDefault();

        var data = this.refs.form.getValues();

        var nameEmptyError = !data.name;

        // Get the names of the files to attach to the sample record.
        data.files = this.state.selected;
        data.paired = this.state.selected.length == 2;

        var readError = data.files.length === 0;

        if (readError || nameEmptyError) {
            this.setState({
                readError: readError,
                nameEmptyError: nameEmptyError
            });
        } else {
            // Send the request to the server.
            this.setState(this.getInitialState(), function () {
                dispatcher.db.samples.request('new', data).success(function () {
                    this.select([]);
                    this.refs.form.clear();
                }, this).failure(function () {
                    this.setState({nameExistsError: true});
                }, this);
            });
        }
    },

    handleExit: function () {
        this.setState(this.getInitialState());
    },

    render: function () {

        var modalBody;

        if (dispatcher.db.hosts.count({added: true}) === 0) {
            modalBody = (
                <Modal.Body>
                    <Alert bsStyle='warning' className='text-center'>
                        <Icon name='notification' />
                        <span> A host genome must be added to Virtool before samples can be created and analyzed.</span>
                    </Alert>
                </Modal.Body>
            );
        } else {
            modalBody = (
                <form onSubmit={this.handleSubmit}>
                    <Modal.Body {...this.props}>
                        <Form
                            ref='form'
                            paired={this.state.selected.length === 2}
                            handleSubmit={this.handleSubmit}
                            {...this.state}
                        />
                        <ReadSelector
                            ref='reads'
                            {...this.state}
                            select={this.select}
                        />
                    </Modal.Body>

                    <Modal.Footer>
                        <PushButton type='submit' bsStyle='primary'>
                            <Icon name='floppy' /> Save
                        </PushButton>
                    </Modal.Footer>
                </form>
            );
        }



        return (
            <Modal dialogClassName='modal-lg' {...this.props} onEntered={this.handleEntered} onExit={this.handleExit}>
                <Modal.Header {...this.props} closeButton>
                    Create Sample
                </Modal.Header>

                {modalBody}
            </Modal>
        );
    }
});

module.exports = SamplesImport;