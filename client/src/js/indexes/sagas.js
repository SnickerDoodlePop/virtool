import { get } from "lodash-es";
import { push } from "connected-react-router";
import { apiCall, setPending } from "../utils/sagas";
import {
    FIND_INDEXES,
    GET_INDEX,
    GET_UNBUILT,
    CREATE_INDEX,
    GET_INDEX_HISTORY,
    LIST_READY_INDEXES,
    WS_INSERT_INDEX,
    WS_UPDATE_INDEX,
    WS_REMOVE_INDEX,
    REFRESH_OTUS,
    GET_REFERENCE
} from "../app/actionTypes";
import * as otusAPI from "../otus/api";
import * as refsAPI from "../references/api";
import * as indexesAPI from "./api";
import { all, put, select, takeEvery, takeLatest } from "redux-saga/effects";

export function* watchIndexes() {
    yield takeLatest(WS_INSERT_INDEX, wsChangeIndexes);
    yield takeLatest(WS_UPDATE_INDEX, wsChangeIndexes);
    yield takeLatest(WS_REMOVE_INDEX, wsChangeIndexes);
    yield takeLatest(FIND_INDEXES.REQUESTED, findIndexes);
    yield takeLatest(GET_INDEX.REQUESTED, getIndex);
    yield takeLatest(GET_UNBUILT.REQUESTED, getUnbuilt);
    yield takeEvery(CREATE_INDEX.REQUESTED, createIndex);
    yield takeLatest(GET_INDEX_HISTORY.REQUESTED, getIndexHistory);
    yield takeLatest(LIST_READY_INDEXES.REQUESTED, listReadyIndexes);
}

export function* wsChangeIndexes(action) {
    // The id of the ref accosicated with the WS update.
    const indexDetailId = action.data.reference.id;

    // The id of the current detailed ref.
    const refId = yield select(state => get(state, "references.detail.id"));

    // Only update ref and indexes if refIds match.
    if (indexDetailId === refId) {
        yield all([
            apiCall(refsAPI.get, { refId }, GET_REFERENCE),
            apiCall(indexesAPI.find, { refId }, FIND_INDEXES),
            apiCall(otusAPI.find, { refId }, REFRESH_OTUS)
        ]);
    }
}

export function* findIndexes(action) {
    yield apiCall(indexesAPI.find, action, FIND_INDEXES);
}

export function* getIndex(action) {
    yield select();
    yield apiCall(indexesAPI.get, action, GET_INDEX);
}

export function* getUnbuilt(action) {
    yield apiCall(indexesAPI.getUnbuilt, action, GET_UNBUILT);
}

export function* listReadyIndexes(action) {
    yield apiCall(indexesAPI.listReady, action, LIST_READY_INDEXES);
}

export function* createIndex(action) {
    const extraFunc = {
        closeModal: put(push({ state: { rebuild: false } }))
    };
    yield setPending(apiCall(indexesAPI.create, action, CREATE_INDEX, {}, extraFunc));
}

export function* getIndexHistory(action) {
    yield setPending(apiCall(indexesAPI.getHistory, action, GET_INDEX_HISTORY));
}
