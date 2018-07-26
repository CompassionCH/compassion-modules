import React from "react";
import PropTypes from "prop-types";
import { withStyles } from "@material-ui/core/styles";
import InputLabel from "@material-ui/core/InputLabel";
import FormControl from "@material-ui/core/FormControl";
import Select from "@material-ui/core/Select";

const styles = theme => ({
    root: {
        display: "flex",
        flexWrap: "wrap"
    },
    formControl: {
        margin: theme.spacing.unit,
        width: '100%'
    },
    selectEmpty: {
        marginTop: theme.spacing.unit * 2
    }
});

class SimpleSelect extends React.Component {
    state = {
        selectValue: "",
    };

    handleChange = event => {
        this.setState({ selectValue: event.target.value });
    };

    render() {
        const { classes } = this.props;

        return (
            <div className={classes.root}>
                <FormControl className={classes.formControl}>
                    <InputLabel htmlFor={this.props.name}>{this.props.text}</InputLabel>
                    <Select
                        native
                        value={this.state.selectValue}
                        onChange={this.handleChange}
                        inputProps={{
                            name: this.props.name,
                            id: this.props.name
                        }}>
                        <option value={''}/>
                        {this.props.elements.map((item, index) => (
                            <option key={index} value={item.value}>{item.text}</option>
                        ))}
                    </Select>
                </FormControl>
            </div>
        );
    }
}

SimpleSelect.propTypes = {
    classes: PropTypes.object.isRequired
};

export default withStyles(styles)(SimpleSelect);
